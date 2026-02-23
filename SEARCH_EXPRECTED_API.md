```py

from ehentai_downloader import Downloader
from json import load
from pydantic import BaseModel

with open("cookies.json", "r") as f:
    cookies = load(f)

class Gallery(BaseModel):
    title: str
    published: datetime
    rate: float
    type: str # western, etc.
    tags: list[str]
    url: str
    thumbnail_url: str
    id: int

class SearchResult(BaseModel):
    galleries: list[Gallery]
    first: int
    last: int

async with Downloader(cookies=cookies) as downloader:
    result: SearchResult = await downloader.search(query="furry yaoi", next=<上一页最后一个画廊的id>)

```
