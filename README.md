# ehentaix

A small async Python library for searching E-Hentai/ExHentai galleries, fetching thumbnails, and downloading album images.

## Features

- Asynchronous `EHentaiClient` supporting `async with`.
- Gallery search across E-Hentai and ExHentai with pagination (`next`).
- Thumbnail fetching with caching per gallery.
- Full album download to a target folder.
- Bounded retries with exponential backoff.
- Platform-aware album-name sanitization.

## Installation

Requires Python `>=3.8`. Install from this directory:

```bash
python -m pip install -e .
```

The package depends on `beautifulsoup4`, `httpx`, and `pydantic` (>= 2.0).

## Quick start

### Search and fetch thumbnails

```python
import asyncio
from ehentaix import EHentaiClient


async def main() -> None:
    async with EHentaiClient() as client:
        result = await client.search("some query")
        for gallery in result.galleries:
            thumb: bytes = await gallery.thumbnail()
            print(gallery.title, gallery.rate, len(thumb))


asyncio.run(main())
```

Search results are paginated. Pass the returned `last` value back as `next` to load the following page, and set `exhentai=True` to search ExHentai (requires cookies).

### Download an album

```python
import asyncio
from ehentaix import EHentaiClient, santize_album_name


async def main() -> None:
    async with EHentaiClient() as client:
        album_name = await client.album(
            "https://e-hentai.org/g/123456/abcdef123456/", "target_folder"
        )
        print(santize_album_name(album_name))


asyncio.run(main())
```

Images are written directly into the caller-provided target folder, and the parsed album name is returned.

### ExHentai access

Pass cookies to the client. The client must not be closed by the library if you supply your own `httpx.AsyncClient`; only internally created clients are closed by `aclose()`/context-manager exit.

```python
import asyncio
import httpx
from ehentaix import EHentaiClient

cookies = {
    "ipb_member_id": "123456",
    "ipb_pass_hash": "abcdef123456",
    "igneous": "abcdef123456",
}


async def main() -> None:
    client = httpx.AsyncClient(cookies=cookies)
    try:
        async with EHentaiClient(client=client) as ehentai:
            result = await ehentai.search("query", exhentai=True)
    finally:
        await client.aclose()


asyncio.run(main())
```

## Public API

Exported from `ehentaix/__init__.py`:

- `EHentaiClient` — async client with `search()`, `fetch_thumbnail()`, and `album()`.
- `Gallery` — a single search result with a cached `thumbnail()` method.
- `SearchResult` — `galleries` plus `first`/`last` pagination indices.
- `santize_album_name(name)` — returns a filesystem-safe album name.

## Development

Live network check scripts are provided:

```bash
python test_search.py
python test_exhentai_search.py  # requires a local cookies.json
```

These scripts execute at import time and require network access; they are not isolated pytest unit tests.

## License

[MIT](LICENSE)
