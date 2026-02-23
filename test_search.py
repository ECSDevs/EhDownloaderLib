import asyncio
from ehentaix import EHentaiClient


async def main():
    async with EHentaiClient() as d:
        result = await d.search(query="furry yaoi")
        print(f"共 {len(result.galleries)} 条结果")
        print(f"first={result.first}, last={result.last}\n")
        for g in result.galleries[:3]:
            print(f"[{g.type}] {g.title}")
            print(f"  id={g.id} rate={g.rate} published={g.published}")
            print(f"  url={g.url}")
            print(f"  thumbnail_url={g._thumb_url}")
            print(f"  thumbnail={len(await g.thumbnail(1))} bytes")
            print(f"  tags={g.tags[:5]}...")
            print()


asyncio.run(main())
