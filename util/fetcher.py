import os
from mitmproxy import http

def response(flow: http.HTTPFlow):
    if "gochiusa.com" in flow.request.host:
        # 自动根据 URL 创建文件夹并保存文件
        path = flow.request.path.replace("/af2026", "").split("?")[0]
        if path == "/" or not path: path = "/index.html"

        save_path = os.path.join("source/2026", path.lstrip("/"))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(flow.response.content)
        print(f"Saved: {flow.request.url}")