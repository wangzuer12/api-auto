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
PROGRESS_FILE = ROOT / "scripts" / "ai_gen" / "progress.json"  # 断点记录文件

env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


# ---------------------- 新增：进度加载/保存函数 ----------------------
def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": []}


def save_progress(item_key: str):
    prog = load_progress()
    if item_key not in prog["completed"]:
        prog["completed"].append(item_key)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(prog, f, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------
def call_deepseek(prompt: str) -> str:
    raw_code = chat(
        prompt=prompt,
        system="""你是接口自动化测试专家。
规则：
1. 生成 pytest+requests+allure 测试代码。
2. fixture必须注入：login_session, test_context。
3. 接口直接使用传入的完整url，不要拼接base_url，不要定义新session，请求全部使用 login_session 发起请求，login_session已经自动携带登录token。
4. 必须使用 test_context.capture() 收集 request、response、payload，用于失败上报，和conftest配套。
5. 只输出 Python 代码，不要解释，不要markdown代码块标记。""",
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
    方案A：保留Postman raw完整url，每个接口自带独立域名
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
    # 核心：读取raw完整url，包含域名，方案A直接使用
    raw_url = url_obj.get("raw", "")

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
        "url": raw_url,  # raw是完整url，带域名
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
        return True  # 返回标记：文件已存在，视为成功

    out_path.write_text(code, encoding="utf-8")
    print(f"  ✅ written: {out_path}")
    return True


def main():
    if not COLLECTION_PATH.exists():
        print(f"❌ Collection 文件不存在: {COLLECTION_PATH}")
        sys.exit(1)

    info, apis = load_collection(COLLECTION_PATH)
    print(f"📦 Collection: {info.get('name')} | 接口数: {len(apis)}")

    progress = load_progress()
    completed_set = set(progress["completed"])
    print(f"📝 已完成接口数量: {len(completed_set)}")

    template = env.get_template("gen_test_case.j2")

    for api in apis:
        # 唯一标识，作为断点key
        item_key = f"{api['method']}|{api['name']}|{api['url']}"
        if item_key in completed_set:
            print(f"✅ 断点跳过已完成接口: {api['method']} {api['name']}")
            continue

        print(f"\ngenerating: {api['method']} {api['name']} {api['url']}")
        try:
            rendered_prompt = template.render(api=api)
            code = call_deepseek(rendered_prompt)
            success = write_test_file(api, code)
            if success:
                save_progress(item_key)
                print(f"📌 已记录到进度，下次运行跳过此接口")
        except Exception as e:
            print(f"❌ 接口生成失败: {api['method']} {api['name']}, error: {str(e)}")
            # 捕获402余额不足，直接终止脚本
            if "402" in str(e) or "Insufficient Balance" in str(e):
                print("💰 检测到余额不足，脚本停止！充值后重新运行，会从当前接口继续")
                sys.exit(1)
            # 其他异常（网络抖动等），继续跑下一个接口，当前接口下次重试
            continue


if __name__ == "__main__":
    main()
