import asyncio
from json import load
from ehentaix import EHentaiClient


async def main():
    with open("cookies.json", "r") as f:
        cookies = load(f)
    async with EHentaiClient(cookies=cookies) as d:
        result = await d.search(query="furry yaoi", exhentai=True, retries=1)
        print(f"共 {len(result.galleries)} 条结果")
        print(f"first={result.first}, last={result.last}\n")
        for g in result.galleries[:3]:
            print(f"[{g.type}] {g.title}")
            print(f"  id={g.id} rate={g.rate} published={g.published}")
            print(f"  url={g.url}")
            print(f"  thumbnail_url={g._thumb_url}")
            print(f"  thumbnail={len(await g.thumbnail())} bytes")
            print(f"  tags={g.tags[:5]}...")
            print()


asyncio.run(main())
