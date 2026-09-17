import os
import json
import re
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ai_gen.llm_client import chat, extract_code
from jinja2 import Environment, FileSystemLoader





ROOT = Path(__file__).resolve().parents[2]
COLLECTION_PATH = ROOT / "collection.json"
TEMPLATE_DIR = ROOT / "scripts" / "ai_gen" / "prompt_templates"
OUTPUT_DIR = ROOT / "tests" / "api"

env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


def call_deepseek(prompt: str) -> str:
    raw_code = chat(
        prompt=prompt,
        system="你是接口自动化测试专家。根据接口信息生成 pytest+requests+allure 测试代码。只输出 Python 代码，不要解释，不要 markdown 代码块标记。",
        model="deepseek-chat",
        temperature=0.1,
        max_tokens=4096,
    )
    return extract_code(raw_code)


def slugify(text: str) -> str:
    text = text or ""
    # 先保留字母数字中文
    text = re.sub(r"[^0-9A-Za-z一-鿿_/\- ]+", "", text)
    text = text.replace(" ", "_").replace("/", "_").replace("-", "_")
    text = re.sub(r"_+", "_", text).strip("_")
    # 如果结果全是中文或空，用简单命名
    if not text or all('\u4e00' <= c <= '\u9fff' for c in text):
        return "api_test"
    return text


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



def write_test_file(api: dict, code: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"test_{slugify(api['name'])}.py"
    out_path = OUTPUT_DIR / fname

    if out_path.exists():
        print(f"  ⏭️ 已存在，跳过: {out_path}")
        return

    out_path.write_text(code, encoding="utf-8")
    print(f"  ✅ written: {out_path}")


def main():

    if not COLLECTION_PATH.exists():
        print(f"❌ Collection 文件不存在: {COLLECTION_PATH}")
        sys.exit(1)

    info, apis = load_collection(COLLECTION_PATH)
    print(f"📦 Collection: {info.get('name')} | 接口数: {len(apis)}")

    template = env.get_template("gen_test_case.j2")

    for api in apis:
        rendered_prompt = template.render(api=api)
        print(f"generating: {api['method']} {api['name']} {api['url']}")

        code = call_deepseek(rendered_prompt)
        write_test_file(api, code)


if __name__ == "__main__":
    main()