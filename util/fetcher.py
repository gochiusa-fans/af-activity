from datetime import datetime
from threading import Event
from urllib.parse import urlparse, unquote
from zoneinfo import ZoneInfo
from loguru import logger
from pathlib import Path
from playwright.sync_api import sync_playwright, Response, Download
import time
import sys

JST = ZoneInfo("Asia/Tokyo")
p = sync_playwright().start()
closed = Event()
target = datetime(datetime.now(JST).year, 4, 1, 0, 0, 0, tzinfo=JST)
data_path = Path(sys.path[0]).parent / "data" / "browser.json"
source_path = Path(sys.path[0]).parent / "source" / str(datetime.now(JST).year)
extract_url = []
force_no_webp_js = r"""(() => {
  // 拦截 window.UsaImageHelper 赋值，强制关闭 webp
  let _helper;
  Object.defineProperty(window, "UsaImageHelper", {
    configurable: true,
    get() { return _helper; },
    set(v) {
      if (v && typeof v === "object") {
        v.supportsWebp = false;
        v.detectWebp = () => Promise.resolve(false);
        const original = v.resolveImageSrc;
        v.resolveImageSrc = function(image, supportsWebp = false) {
          // 强制按非webp路径返回
          if (!Array.isArray(image)) return image;
          return image[0];
        };
      }
      _helper = v;
    }
  });
})();"""


def fetch(response: Response):
    parse = urlparse(response.url)
    if parse.hostname != "gochiusa.com":
        if parse.hostname != "www.googletagmanager.com":
            extract_url.append(response.url)
        return
    path = unquote(parse.path).replace("/af2026", "")
    if path == "/":
        path += "index.html"
    save_path = source_path / path.lstrip("/")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving {response.url} to {save_path}")
    save_path.write_bytes(response.body())


def download(response: Download):
    parse = urlparse(response.url)
    path = unquote(parse.path).replace("/af2026", "")
    save_path = source_path / path.lstrip("/")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving {response.url} to {save_path}")
    response.save_as(str(save_path))


logger.info("Waiting for April Fools Day...")
while True:
    now = datetime.now(JST)
    if now >= target:
        break
    time.sleep(1)
logger.success("April Fools Day has arrived! Now open the official page.")
browser = p.chromium.launch(headless=False)
browser.on("disconnected", lambda *args: closed.set())
if data_path.exists():
    context = browser.new_context(storage_state=data_path)
else:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    context = browser.new_context()
page = context.new_page()
page.route("**/*", lambda route: route.continue_())
page.add_init_script(force_no_webp_js)
page.on("response", fetch)
page.on("download", download)
page.goto("https://gochiusa.com/af2026/")
page.wait_for_timeout(1000 * 60 * 30)
closed.wait()
logger.info("Browser closed. Saving storage state...")
context.storage_state(path=data_path)
browser.close()
p.stop()
if len(extract_url) != 0:
    logger.warning("The following URLs were extracted during the process:")
    for url in extract_url:
        logger.warning(url)
logger.info("Done!")
