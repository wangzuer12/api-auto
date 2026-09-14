import os
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

ROOT = Path(__file__).resolve().parents[2]
COLLECTION_PATH = ROOT / "collection.json"
TEMPLATE_DIR = ROOT / "scripts" / "ai_gen" / "prompt_templates"
OUTPUT_DIR = ROOT / "tests" / "api"

env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


def call_deepseek(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是接口自动化测试专家，根据 Postman 接口信息生成 pytest+requests+allure 测试代码。只输出 Python 代码，不要解释，不要 ```python 包裹。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=4096,
    )
    return resp.choices[0].message.content


def slugify(text: str) -> str:
    text = text or ""
    text = re.sub(r"[^0-9A-Za-z一-鿿_/\- ]+", "", text)
    text = text.replace(" ", "_").replace("/", "_").replace("-", "_")
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "api"


def normalize_item(item):
    """
    兼容 Postman collection v2.1 结构：
    item 可能是文件夹（有 item 列表），也可能是接口请求。
    """
    requests = []

    if "item" in item:
        for sub in item["item"]:
            requests += normalize_item(sub)
        return requests

    request = item.get("request") or {}
    name = item.get("name", "")
    method = (request.get("method") or "GET").upper()
    url_obj = request.get("url") or {}
    raw_url = url_obj.get("raw") or url_obj.get("path") or ""

    body = request.get("body") or {}
    body_data = None
    if body.get("mode") == "raw":
        body_data = body.get("raw")
    elif body.get("mode") == "json":
        body_data = body.get("raw")
    elif body.get("mode") == "formdata":
        body_data = body.get("formdata")

    params = url_obj.get("query") or []
    headers = request.get("header") or []

    requests.append({
        "name": name,
        "method": method,
        "url": raw_url,
        "params": params,
        "headers": headers,
        "body": body_data,
        "postman_item": item,
    })
    return requests


def load_collection(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("item") or []
    requests = []
    for it in items:
        requests += normalize_item(it)
    return data.get("info", {}), requests


def build_prompt(template_name: str, api: dict) -> str:
    tpl = env.get_template(template_name)
    return tpl.render(api=api)


def extract_python_code(text: str) -> str:
    text = text.strip()
    # 如果模型还是包了代码块，去掉
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def write_test_file(api: dict, code: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"test_{slugify(api['name'])}.py"
    # 避免重名覆盖可加序号，这里简单处理
    out_path = OUTPUT_DIR / fname
    out_path.write_text(code, encoding="utf-8")
    print(f"written: {out_path}")


def main():
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY is empty. Check .env or environment.", file=sys.stderr)
        sys.exit(1)

    if not COLLECTION_PATH.exists():
        print(f"collection.json not found: {COLLECTION_PATH}", file=sys.stderr)
        sys.exit(1)

    info, apis = load_collection(COLLECTION_PATH)
    print(f"collection: {info.get('name')}, apis: {len(apis)}")

    for api in apis:
        print(f"generating: {api['method']} {api['name']} {api['url']}")
        prompt = build_prompt("gen_test_case.j2", api)
        code = call_deepseek(prompt)
        code = extract_python_code(code)
        write_test_file(api, code)


if __name__ == "__main__":
    main()