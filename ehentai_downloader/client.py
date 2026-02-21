import asyncio
import random
from typing import Callable, Any

from httpx import Response, AsyncClient, Cookies

from .config import (
    CONNECTION_TIMEOUT,
    RATE_LIMIT_SLEEP,
    HTTP_RATE_LIMIT,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def fetch_with_retry(
    client: AsyncClient,
    url: str,
    retries: int = 5,
    on_retry: Callable[[int, int, Exception], None] | None = None,
) -> Response | None:
    cookies_to_send = getattr(client, "_eh_cookies", None)
    for attempt in range(retries):
        try:
            response = await client.get(
                url,
                headers=HEADERS,
                timeout=CONNECTION_TIMEOUT,
                cookies=cookies_to_send,
            )
            _ = response.raise_for_status()
            if response.status_code == HTTP_RATE_LIMIT:
                await asyncio.sleep(RATE_LIMIT_SLEEP)
            return response
        except Exception as e:
            if on_retry:
                on_retry(attempt, retries, e)
            if attempt < retries - 1:
                delay = 2 ** (attempt + 1) + random.uniform(1, 2)
                await asyncio.sleep(delay)
    return None


def create_client(
    cookies: dict[str, str] | Cookies | None = None, **kwargs: Any
) -> AsyncClient:
    default_kwargs = {
        "timeout": CONNECTION_TIMEOUT,
        "follow_redirects": True,
    }
    default_kwargs.update(kwargs)
    client = AsyncClient(**default_kwargs)
    if cookies is not None:
        client._eh_cookies = cookies
    return client
