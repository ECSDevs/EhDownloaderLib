import asyncio
from ehentai_downloader import download_album, download_albums


async def single_album_example():
    url = "https://e-hentai.org/g/3801320/2a137d555b/"

    def on_progress(page, pic, total):
        print(f"[Progress] Page {page}, Image {pic}/{total}")

    def on_log(event, details):
        print(f"[{event}] {details}")

    print("\n=== Single Album Download ===\n")
    result = await download_album(
        url=url,
        download_folder="Downloads",
        on_progress=on_progress,
        on_log=on_log,
    )

    print(f"\nDownload Result:")
    print(f"Album Name: {result['album_name']}")
    print(f"Download Path: {result['download_path']}")
    print(f"Success: {result['success']}")
    print(f"Failed Downloads: {len(result['failed_downloads'])}")


async def single_album_with_cookies_example():
    url = "https://exhentai.org/g/3283010/33f0d1d60c/"

    def on_progress(page, pic, total):
        print(f"[Progress] Page {page}, Image {pic}/{total}")

    def on_log(event, details):
        print(f"[{event}] {details}")

    # Example cookies - replace with your actual cookies
    cookies = {
        "ipb_member_id": "9344715",
        "ipb_pass_hash": "ca2fe5bc1af6fd182fd4831f2d27094a",
        "igneous": "kzujocikh8jbpc1p6",
    }

    print("\n=== Single Album Download with Cookies ===\n")
    result = await download_album(
        url=url,
        download_folder="Downloads",
        cookies=cookies,
        on_progress=on_progress,
        on_log=on_log,
    )

    print(f"\nDownload Result:")
    print(f"Album Name: {result['album_name']}")
    print(f"Download Path: {result['download_path']}")
    print(f"Success: {result['success']}")
    print(f"Failed Downloads: {len(result['failed_downloads'])}")


async def batch_download_example():
    urls = [
        "https://e-hentai.org/g/3392858/1a77348e16/",
    ]

    def on_progress(page, pic, total):
        print(f"[Progress] Page {page}, Image {pic}/{total}")

    def on_log(event, details):
        print(f"[{event}] {details}")

    print("\n=== Batch Album Download ===\n")
    results = await download_albums(
        urls=urls,
        download_folder="Downloads",
        on_progress=on_progress,
        on_log=on_log,
    )

    print(f"\nAll Downloads Complete:")
    for i, result in enumerate(results):
        print(f"\nAlbum {i + 1}:")
        print(f"  Name: {result['album_name']}")
        print(f"  Success: {result['success']}")


if __name__ == "__main__":
    print("EHentai Downloader - Async Example")
    print("=" * 40)
    asyncio.run(single_album_example())
    # Uncomment to test cookies
    # asyncio.run(single_album_with_cookies_example())
