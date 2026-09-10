import os
import sys
import time
import hmac
import hashlib
import base64
import urllib.parse
import json
import urllib.request

webhook = os.environ["DING_WEBHOOK"]
secret = os.environ["DING_SECRET"]

with open("ding_msg.txt", encoding="utf-8") as f:
    text = f.read().strip()

timestamp = str(round(time.time() * 1000))
string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
sign = base64.b64encode(
    hmac.new(secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
).decode("utf-8")
sign = urllib.parse.quote_plus(sign)

url = f"{webhook}&timestamp={timestamp}&sign={sign}"

payload = {
    "msgtype": "markdown",
    "markdown": {
        "title": "API 自动化构建通知",
        "text": text
    }
}

data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    resp = urllib.request.urlopen(req, timeout=10)
    print(resp.read().decode("utf-8"))
except Exception as e:
    print("dingtalk notify failed:", e)