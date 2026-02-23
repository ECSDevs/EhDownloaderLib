```py
from ehentai_downloader import Downloader
from httpx import AsyncClient

cookies = {
    "ipb_member_id": "123456",
    "ipb_pass_hash": "abcdef123456",
    "igneous": "abcdef123456",
}



async def main():
    # Way 1
    client = AsyncClient(cookies=cookies)
    downloader = Downloader(client=client)
    r: str = await downloader.album('https://e-hentai.org/g/123456/abcdef123456/', 'target_folder')
    await client.aclose()

    # Way 2
    async with Downloader(cookies=cookies) as downloader:
        r: str = await downloader.album('https://e-hentai.org/g/123456/abcdef123456/', 'target_folder')

    # Returns album name if successful, otherwise raises an exception
    # should provide a name santizer

    from ehentai_downloader import santize_album_name

    available_filename = f'{santize_album_name(r)}.7z'

    # all the files should be in the target_folder, not target_folder/album_name

```

Other unnecessary classes, functions, and variables should be removed.
Simplize the project as much as possible.
