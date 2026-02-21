import asyncio
import random
from typing import Optional, Callable, Dict, Any, Union
from urllib.parse import urlparse

import httpx
from httpx import Response, AsyncClient, Cookies

from .config import (
    CONNECTION_TIMEOUT,
    RATE_LIMIT_SLEEP,
    HTTP_RATE_LIMIT,
    random_user_agent,
)


def make_headers(url: str) -> Dict[str, str]:
    host = urlparse(url).netloc
    return {
        "Host": host,
        "User-Agent": random_user_agent(),
        "Accept": (
            "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5"
        ),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://e-hentai.org/",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }


async def fetch_with_retry(
    client: AsyncClient,
    url: str,
    retries: int = 5,
    on_retry: Optional[Callable[[int, int, Exception], None]] = None,
) -> Optional[Response]:
    last_error: Optional[Exception] = None
    for attempt in range(retries):
        try:
            headers = make_headers(url)
            response = await client.get(
                url, headers=headers, timeout=CONNECTION_TIMEOUT
            )
            response.raise_for_status()
            if response.status_code == HTTP_RATE_LIMIT:
                await asyncio.sleep(RATE_LIMIT_SLEEP)
            return response
        except Exception as e:
            last_error = e
            if on_retry:
                on_retry(attempt, retries, e)
            if attempt < retries - 1:
                delay = 2 ** (attempt + 1) + random.uniform(1, 2)
                await asyncio.sleep(delay)
    return None


def create_client(
    cookies: Optional[Union[Dict[str, str], Cookies]] = None, **kwargs: Any
) -> AsyncClient:
    default_kwargs = {
        "timeout": CONNECTION_TIMEOUT,
        "follow_redirects": True,
    }
    if cookies is not None:
        default_kwargs["cookies"] = cookies
    default_kwargs.update(kwargs)
    return AsyncClient(**default_kwargs)
