import re
from typing import List, cast
from urllib.parse import urlparse, parse_qs, urlencode

import httpx
from bs4 import BeautifulSoup, Tag

from .client import fetch_with_retry


async def fetch_page(client: httpx.AsyncClient, url: str) -> BeautifulSoup:
    response = await fetch_with_retry(client, url)
    if response is None:
        raise ValueError(f"Failed to fetch page: {url}")
    return BeautifulSoup(response.text, "html.parser")


def extract_album_name(url: str, soup: BeautifulSoup) -> str:
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")
    url_path_id = f"{path_parts[0]}_{path_parts[1]}_{path_parts[2]}"
    title_container = soup.find("h1", {"id": "gn"})
    album_name = title_container.get_text() if title_container else "unknown_album"
    return f"{album_name}_{url_path_id}"


def extract_album_pages(url: str, soup: BeautifulSoup) -> List[str]:
    pattern = re.compile(f"^{re.escape(url)}\\?p=")
    next_pages = soup.find_all("a", {"href": pattern, "onclick": "return false"})
    if not next_pages or len(next_pages) < 2:
        return []
    last_page_tag = cast(Tag, next_pages[-2])
    last_page_url = cast(str, last_page_tag.get("href"))
    if not last_page_url:
        return []
    match = re.search(r"\?p=(\d+)", last_page_url)
    last_page = int(match.group(1)) if match else 0
    album_pages = [f"{url}?p={page}" for page in range(1, last_page)]
    album_pages.append(last_page_url)
    return album_pages


def extract_picture_pages(containers: List[Tag]) -> List[str]:
    result = []
    for container in containers:
        href = cast(str, container.get("href"))
        if href and "/s/" in href:
            result.append(href)
    return result


async def get_reloaded_picture_page(
    client: httpx.AsyncClient, picture_page: str
) -> str:
    soup = await fetch_page(client, picture_page)
    nl_container = soup.find("a", {"id": "loadfail", "onclick": True})
    if not nl_container:
        return picture_page
    nl_container = cast(Tag, nl_container)
    onclick_attr = cast(str, nl_container.get("onclick"))
    if not onclick_attr:
        return picture_page
    nl_match = re.search(r"nl\('([^']+)'\)", onclick_attr)
    if not nl_match:
        return picture_page
    nl_value = nl_match.group(1)
    parsed_url = urlparse(picture_page)
    query_params = parse_qs(parsed_url.query)
    query_params["nl"] = nl_value
    return parsed_url._replace(query=urlencode(query_params, doseq=True)).geturl()


async def extract_image_url(client: httpx.AsyncClient, page_url: str) -> str:
    soup = await fetch_page(client, page_url)
    img_tag = soup.find("img", {"id": "img", "src": True})
    if not img_tag:
        raise ValueError(f"Could not find image tag on page: {page_url}")
    img_tag = cast(Tag, img_tag)
    src = cast(str, img_tag.get("src"))
    if not src:
        raise ValueError(f"Image tag has no src attribute: {page_url}")
    return src
