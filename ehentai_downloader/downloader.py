import asyncio
import os
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, cast
from urllib.parse import urlparse, parse_qs, urlencode

import httpx
from bs4 import BeautifulSoup, Tag

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT = 30.0
CHUNK_SIZE = 16 * 1024


def santize_album_name(name: str) -> str:
    invalid = r'[\\/:*?"<>|]' if os.name == "nt" else r"[/:]"
    return re.sub(invalid, "_", name)


class Downloader:
    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        self._client = client
        self._cookies = cookies
        self._owns_client = client is None

    async def __aenter__(self) -> "Downloader":
        if self._owns_client:
            self._client = httpx.AsyncClient(
                timeout=TIMEOUT, follow_redirects=True, cookies=self._cookies
            )
        return self

    async def __aexit__(self, *args) -> None:
        if self._owns_client and self._client:
            await self._client.aclose()

    async def _get(self, url: str, retries: int = 5) -> httpx.Response:
        for attempt in range(retries):
            try:
                r = await self._client.get(url, headers=HEADERS, timeout=TIMEOUT)
                r.raise_for_status()
                return r
            except Exception:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** (attempt + 1) + random.uniform(1, 2))

    async def _fetch_soup(self, url: str) -> BeautifulSoup:
        r = await self._get(url)
        return BeautifulSoup(r.text, "html.parser")

    async def album(self, url: str, target_folder: str) -> str:
        soup = await self._fetch_soup(url)
        title_el = soup.find("h1", {"id": "gn"})
        album_name = title_el.get_text() if title_el else "unknown_album"

        Path(target_folder).mkdir(parents=True, exist_ok=True)

        pages = [url] + self._extract_album_pages(url, soup)
        for i, page_url in enumerate(pages):
            page_soup = await self._fetch_soup(page_url) if i > 0 else soup
            links = cast(List[Tag], page_soup.find_all("a", {"href": True}))
            pic_pages = [
                cast(str, a.get("href"))
                for a in links
                if "/s/" in cast(str, a.get("href", ""))
            ]
            for pic_url in pic_pages:
                img_url = await self._resolve_image(pic_url)
                await self._download_image(img_url, target_folder)
                await asyncio.sleep(random.uniform(1.5, 4.0))
            if i < len(pages) - 1:
                await asyncio.sleep(random.uniform(1, 5))

        return album_name

    def _extract_album_pages(self, url: str, soup: BeautifulSoup) -> List[str]:
        pattern = re.compile(f"^{re.escape(url)}\\?p=")
        tags = soup.find_all("a", {"href": pattern, "onclick": "return false"})
        if not tags or len(tags) < 2:
            return []
        last_url = cast(str, cast(Tag, tags[-2]).get("href"))
        m = re.search(r"\?p=(\d+)", last_url)
        last = int(m.group(1)) if m else 0
        return [f"{url}?p={p}" for p in range(1, last)] + [last_url]

    async def _resolve_image(self, pic_page: str) -> str:
        soup = await self._fetch_soup(pic_page)
        nl = soup.find("a", {"id": "loadfail", "onclick": True})
        if nl:
            onclick = cast(str, cast(Tag, nl).get("onclick", ""))
            m = re.search(r"nl\('([^']+)'\)", onclick)
            if m:
                parsed = urlparse(pic_page)
                q = parse_qs(parsed.query)
                q["nl"] = m.group(1)
                pic_page = parsed._replace(query=urlencode(q, doseq=True)).geturl()
                soup = await self._fetch_soup(pic_page)

        img = soup.find("img", {"id": "img", "src": True})
        if not img:
            raise ValueError(f"No image found on: {pic_page}")
        return cast(str, cast(Tag, img).get("src"))

    async def _download_image(self, url: str, folder: str) -> None:
        r = await self._get(url)
        filename = url.split("/")[-1]
        filepath = Path(folder) / filename
        with open(filepath, "wb") as f:
            f.write(r.content)
