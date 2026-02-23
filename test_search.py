import asyncio
from ehentai_downloader import Downloader


async def main():
    async with Downloader() as d:
        result = await d.search(query="furry yaoi")
        print(f"共 {len(result.galleries)} 条结果")
        print(f"first={result.first}, last={result.last}\n")
        for g in result.galleries[:3]:
            print(f"[{g.type}] {g.title}")
            print(f"  id={g.id} rate={g.rate} published={g.published}")
            print(f"  url={g.url}")
            print(f"  thumbnail={g.thumbnail_url}")
            print(f"  tags={g.tags[:5]}...")
            print()


asyncio.run(main())
