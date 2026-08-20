from __future__ import annotations

import asyncio
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import cast, Any
from urllib.parse import urlparse, parse_qs, urlencode

import httpx
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, field

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT = 30.0
CHUNK_SIZE = 16 * 1024


@dataclass
class Gallery:
    title: str
    published: datetime
    rate: float
    type: str
    tags: list[str]
    url: str
    id: int
    filecount: int
    _client: EHentaiClient = field(repr=False)
    _thumb_url: str = field(repr=False)
    _thumb_cache: bytes | None = field(default=None, repr=False, init=False)

    async def thumbnail(self, retries: int = 5) -> bytes:
        if self._thumb_cache is None:
            self._thumb_cache = await self._client.fetch_thumbnail(
                self._thumb_url, retries
            )
        return self._thumb_cache


@dataclass
class SearchResult:
    galleries: list[Gallery]
    first: int
    last: int


def _parse_rating(style: str) -> float:
    m = re.search(r"background-position:(-?\d+)px (-?\d+)px", style)
    if not m:
        return 0.0
    x, y = int(m.group(1)), int(m.group(2))
    rating = 5.0 + x / 16
    if y == -1:
        rating += 0.5
    return round(rating, 1)


def santize_album_name(name: str) -> str:
    invalid = r'[\\/:*?"<>|]' if os.name == "nt" else r"[/:]"
    return re.sub(invalid, "_", name)


class EHentaiClient:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cookies: dict[str, str] | None = None,
    ):
        self._client = client or httpx.AsyncClient(
            cookies=cookies, follow_redirects=True, timeout=TIMEOUT
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "EHentaiClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def _get(self, url: str, retries: int = 5) -> httpx.Response:
        attempt = 0
        while attempt < retries:
            try:
                r = await self._client.get(url, headers=HEADERS, timeout=TIMEOUT)
                r.raise_for_status()
                return r
            except Exception:
                attempt += 1
                if attempt >= retries:
                    raise
                await asyncio.sleep(2 ** (attempt + 1) + random.uniform(1, 2))
        raise RuntimeError("Retries must bigger than 0")

    async def _fetch_soup(self, url: str, retries: int = 5) -> BeautifulSoup:
        r = await self._get(url, retries)
        return BeautifulSoup(r.text, "html.parser")

    async def search(
        self,
        query: str,
        next: int | None = None,
        exhentai: bool = False,
        retries: int = 5,
    ) -> SearchResult:
        params = {"f_search": query}
        if next is not None:
            params["next"] = str(next)
        base = "https://exhentai.org" if exhentai else "https://e-hentai.org"
        url = base + "/?" + urlencode(params)
        soup = await self._fetch_soup(url, retries)
        return await self._parse_search_results(soup, retries)

    async def fetch_thumbnail(self, url: str, retries: int = 5) -> bytes:
        if not url:
            return b""
        r = await self._get(url, retries)
        return r.content

    async def _parse_search_results(
        self, soup: BeautifulSoup, retries: int = 5
    ) -> SearchResult:
        entries: list[tuple[dict[str, Any], str]] = []
        rows = soup.select("table.itg tr")[1:]  # skip header
        for row in rows:
            name_td = row.select_one("td.gl3c.glname")
            if not name_td:
                continue
            a = cast(Tag, name_td.find("a", href=True))
            if not a:
                continue
            href = cast(str, a.get("href", ""))
            gid_m = re.search(r"/g/(\d+)/", href)
            if not gid_m:
                continue
            gid = int(gid_m.group(1))
            pages_el = row.find("div", string=re.compile(r"^\d+\s+pages?$"))
            if pages_el:
                pages_m = re.search(r"\d+", pages_el.get_text(strip=True))
                filecount = int(pages_m.group(0)) if pages_m else 0
            else:
                filecount = 0
            title = a.select_one("div.glink")
            title_text = title.get_text(strip=True) if title else ""
            tags = [
                cast(str, t.get("title", ""))
                for t in a.select("div.gt")
                if t.get("title")
            ]
            cat_div = row.select_one("td.gl1c div.cn")
            gallery_type = cat_div.get_text(strip=True) if cat_div else ""
            posted_div = row.select_one(f"div[id='posted_{gid}']")
            published = (
                datetime.strptime(posted_div.get_text(strip=True), "%Y-%m-%d %H:%M")
                if posted_div
                else datetime.min
            )
            ir_div = row.select_one("td.gl2c > div:last-child div.ir")
            rate = _parse_rating(cast(str, ir_div.get("style", ""))) if ir_div else 0.0
            thumb_td = row.select_one("td.gl2c div.glthumb img")
            thumb_url = (
                cast(str, thumb_td.get("data-src") or thumb_td.get("src", ""))
                if thumb_td
                else ""
            )
            entries.append(
                (
                    dict(
                        title=title_text,
                        published=published,
                        rate=rate,
                        type=gallery_type,
                        tags=tags,
                        url=href,
                        id=gid,
                        filecount=filecount,
                    ),
                    thumb_url,
                )
            )
        galleries = [
            Gallery(**data, _client=self, _thumb_url=thumb_url)
            for data, thumb_url in entries
        ]
        first = galleries[0].id if galleries else 0
        last = galleries[-1].id if galleries else 0
        return SearchResult(galleries=galleries, first=first, last=last)

    async def album(self, url: str, target_folder: str, retries: int = 5) -> str:
        soup = await self._fetch_soup(url, retries)
        title_el = soup.find("h1", {"id": "gn"})
        album_name = title_el.get_text() if title_el else "unknown_album"

        Path(target_folder).mkdir(parents=True, exist_ok=True)

        pages = [url] + self._extract_album_pages(url, soup)
        for i, page_url in enumerate(pages):
            page_soup = await self._fetch_soup(page_url, retries) if i > 0 else soup
            links = cast(list[Tag], page_soup.find_all("a", {"href": True}))
            pic_pages = [
                cast(str, a.get("href"))
                for a in links
                if "/s/" in cast(str, a.get("href", ""))
            ]
            for pic_url in pic_pages:
                img_url = await self._resolve_image(pic_url, retries)
                await self._download_image(img_url, target_folder, retries)
                await asyncio.sleep(random.uniform(1.5, 4.0))
            if i < len(pages) - 1:
                await asyncio.sleep(random.uniform(1, 5))

        return album_name

    def _extract_album_pages(self, url: str, soup: BeautifulSoup) -> list[str]:
        pattern = re.compile(f"^{re.escape(url)}\\?p=")
        tags = soup.find_all("a", {"href": pattern, "onclick": "return false"})
        if not tags or len(tags) < 2:
            return []
        last_url = cast(str, cast(Tag, tags[-2]).get("href"))
        m = re.search(r"\?p=(\d+)", last_url)
        last = int(m.group(1)) if m else 0
        return [f"{url}?p={p}" for p in range(1, last)] + [last_url]

    async def _resolve_image(self, pic_page: str, retries: int = 5) -> str:
        soup = await self._fetch_soup(pic_page, retries)
        nl = soup.find("a", {"id": "loadfail", "onclick": True})
        if nl:
            onclick = cast(str, cast(Tag, nl).get("onclick", ""))
            m = re.search(r"nl\('([^']+)'\)", onclick)
            if m:
                parsed = urlparse(pic_page)
                q: dict[str, Any] = parse_qs(parsed.query)
                q["nl"] = m.group(1)
                pic_page = parsed._replace(query=urlencode(q, doseq=True)).geturl()
                soup = await self._fetch_soup(pic_page, retries)

        img = soup.find("img", {"id": "img", "src": True})
        if not img:
            raise ValueError(f"No image found on: {pic_page}")
        return cast(str, cast(Tag, img).get("src"))

    async def _download_image(self, url: str, folder: str, retries: int = 5) -> None:
        r = await self._get(url, retries)
        filename = url.split("/")[-1]
        filepath = Path(folder) / filename
        with open(filepath, "wb") as f:
            f.write(r.content)
