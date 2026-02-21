import asyncio
import random
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any, cast, Union

import httpx
from httpx import Cookies
from bs4 import Tag

from .client import create_client, fetch_with_retry
from .crawler import (
    fetch_page,
    extract_album_name,
    extract_album_pages,
    extract_picture_pages,
    get_reloaded_picture_page,
    extract_image_url,
)
from .fileio import ensure_download_dir, get_filename_from_url
from .config import CHUNK_SIZE


class AsyncAlbumDownloader:
    def __init__(
        self,
        url: str,
        download_folder: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        cookies: Optional[Union[Dict[str, str], Cookies]] = None,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
    ):
        self.url = url
        self.download_folder = download_folder
        self.cookies = cookies
        self._client = client
        self._owns_client = client is None
        self.on_progress = on_progress
        self.on_log = on_log
        self.album_name: str = ""
        self.download_path: str = ""
        self.failed_downloads: List[str] = []

    async def _log(self, event: str, details: str) -> None:
        if self.on_log:
            if asyncio.iscoroutinefunction(self.on_log):
                await self.on_log(event, details)
            else:
                self.on_log(event, details)

    async def _progress(self, page: int, pic: int, total: int) -> None:
        if self.on_progress:
            if asyncio.iscoroutinefunction(self.on_progress):
                await self.on_progress(page, pic, total)
            else:
                self.on_progress(page, pic, total)

    async def __aenter__(self) -> "AsyncAlbumDownloader":
        if self._owns_client:
            self._client = create_client(cookies=self.cookies)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._owns_client and self._client:
            await self._client.aclose()

    async def download(self) -> Dict[str, Any]:
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use async with context manager."
            )

        await self._log("Starting", f"Initializing download for: {self.url}")

        initial_soup = await fetch_page(self._client, self.url)
        self.album_name = extract_album_name(self.url, initial_soup)
        self.download_path = ensure_download_dir(self.album_name, self.download_folder)

        await self._log(
            "Album Info", f"Name: {self.album_name}, Path: {self.download_path}"
        )

        album_pages = [self.url] + extract_album_pages(self.url, initial_soup)
        self.failed_downloads = []

        for page_idx, page_url in enumerate(album_pages):
            await self._log(
                "Processing page", f"Page {page_idx + 1}/{len(album_pages)}"
            )
            page_soup = await fetch_page(self._client, page_url)
            containers = cast(List[Tag], page_soup.find_all("a", {"href": True}))
            picture_pages = extract_picture_pages(containers)
            await self._process_pictures(page_idx + 1, picture_pages)
            if page_idx < len(album_pages) - 1:
                await asyncio.sleep(random.uniform(1, 5))

        result = {
            "album_name": self.album_name,
            "download_path": self.download_path,
            "failed_downloads": self.failed_downloads,
            "success": len(self.failed_downloads) == 0,
        }
        await self._log("Complete", f"Success: {result['success']}")
        return result

    async def _process_pictures(self, page_num: int, picture_pages: List[str]) -> None:
        if self._client is None:
            raise RuntimeError("Client not initialized")
        for pic_idx, pic_url in enumerate(picture_pages):
            try:
                reloaded_url = await get_reloaded_picture_page(self._client, pic_url)
                image_url = await extract_image_url(self._client, reloaded_url)
                await self._download_image(
                    page_num, pic_idx + 1, len(picture_pages), image_url
                )
                await asyncio.sleep(random.uniform(1.5, 4.0))
            except Exception as e:
                await self._log("Error", f"Failed to download {pic_url}: {str(e)}")
                self.failed_downloads.append(pic_url)

    async def _download_image(self, page: int, pic: int, total: int, url: str) -> None:
        if self._client is None:
            raise RuntimeError("Client not initialized")
        response = await fetch_with_retry(self._client, url)
        if response is None:
            self.failed_downloads.append(url)
            await self._log("Download failed", f"Could not download: {url}")
            return

        filename = get_filename_from_url(url)
        filepath = Path(self.download_path) / filename

        with open(filepath, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                f.write(chunk)

        await self._progress(page, pic, total)


async def download_album(
    url: str,
    download_folder: Optional[str] = None,
    cookies: Optional[Union[Dict[str, str], Cookies]] = None,
    on_progress: Optional[Callable[[int, int, int], None]] = None,
    on_log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    async with AsyncAlbumDownloader(
        url,
        download_folder=download_folder,
        cookies=cookies,
        on_progress=on_progress,
        on_log=on_log,
    ) as downloader:
        return await downloader.download()


async def download_albums(
    urls: List[str],
    download_folder: Optional[str] = None,
    cookies: Optional[Union[Dict[str, str], Cookies]] = None,
    on_progress: Optional[Callable[[int, int, int], None]] = None,
    on_log: Optional[Callable[[str, str], None]] = None,
) -> List[Dict[str, Any]]:
    async with create_client(cookies=cookies) as client:
        results = []
        for url in urls:
            async with AsyncAlbumDownloader(
                url,
                download_folder=download_folder,
                client=client,
                on_progress=on_progress,
                on_log=on_log,
            ) as downloader:
                result = await downloader.download()
                results.append(result)
        return results
