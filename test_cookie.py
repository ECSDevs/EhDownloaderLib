import httpx

url = "https://exhentai.org/g/3283010/33f0d1d60c/"

cookies = {
    "ipb_member_id": "9344715",
    "ipb_pass_hash": "ca2fe5bc1af6fd182fd4831f2d27094a",
    "igneous": "kzujocikh8jbpc1p6",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = httpx.get(url, cookies=cookies, headers=headers)

print(response.text)
