from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo
from pyquery import PyQuery
from datetime import datetime
from loguru import logger
from pathlib import Path
import sys
import httpx

JST = ZoneInfo("Asia/Tokyo")
file_path = Path(sys.path[0]).parent / "source" / str(datetime.now(JST).year) / "index.html"
client = httpx.Client(headers={
    "User-Agent": "GClient/2026.04"
})
doc = PyQuery(file_path.read_text("utf-8"))


def fetch(url: str):
    if url.startswith("#"):
        return
    res = client.get(f"https://gochiusa.com/af2026/{url}")
    if res.status_code != 200:
        logger.error(f"Failed to fetch {url}: {res.status_code}")
        return
    save_path = file_path.parent / unquote(urlparse(url).path.lstrip("/af2026"))
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(res.content)
    logger.success(f"Saved {url} to {save_path}")


logger.info("Begin to refetch the leak one")
for item in doc('link').items():
    href = item.attr('href')
    if href:
        fetch(href)
for item in doc('meta[name^="msapplication"]').items():
    content = item.attr('content')
    if content:
        fetch(content)

