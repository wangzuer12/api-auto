import json
import re
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from .llm_client import chat

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_AI_GEN = ROOT / "scripts" / "ai_gen"
PROMPT_DIR = SCRIPTS_AI_GEN / "prompt_templates"
OUTPUT_DIR = ROOT / "reports" / "ai-failure-analysis"
FAILURES_PATH = ROOT / "reports" / "failures.json"

env = Environment(
    loader=FileSystemLoader(str(PROMPT_DIR), encoding="utf-8"),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

template = env.get_template("analyze_failure.j2")


def safe_name(value: str, max_len: int = 120) -> str:
    # 清洗 Windows/URL/pytest nodeid 不友好字符
    bad = '<>:"/\\|?*[]'
    name = "".join("_" if ch in bad or ord(ch) < 32 else ch for ch in value)
    name = name.replace("::", "__").replace("[", "_").replace("]", "_")
    name = re.sub(r"_+", "_", name).strip("_. ")
    # 把 \u6b63 这种也替换掉，避免奇怪显示/边界问题
    name = name.replace("\\u", "_u")
    return (name[:max_len]) or "failure"


def load_failures_json(path: Path) -> list:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def analyze_one(failure: dict) -> str:
    prompt = template.render(failure=failure)
    return chat(
        prompt=prompt,
        system="你是接口自动化测试失败分析专家，擅长根据用例、请求、响应、断言错误和堆栈定位原因。",
        temperature=0.2,
        max_tokens=4096,
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = load_failures_json(FAILURES_PATH)
    if not failures:
        print("✅ 没有失败数据可分析，检查 reports/failures.json")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_parts = [f"# AI 失败分析报告 {ts}\n"]
    results = []

    for i, failure in enumerate(failures, 1):
        test_name = failure.get("test_name", f"failure_{i}")
        print(f"analyzing failure {i}/{len(failures)}: {test_name}")

        analysis = analyze_one(failure)
        results.append((test_name, analysis))

        single_path = OUTPUT_DIR / f"{ts}_{safe_name(test_name)}.md"
        single_path.parent.mkdir(parents=True, exist_ok=True)
        single_path.write_text(analysis, encoding="utf-8")
        print(f"  ✅ written: {single_path}")

        all_parts.append(f"## {i}. {test_name}\n")
        all_parts.append(analysis)
        all_parts.append("\n---\n")

    summary_path = OUTPUT_DIR / f"ai_failure_analysis_{ts}.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(all_parts), encoding="utf-8")
    print(f"✅ summary: {summary_path}")


if __name__ == "__main__":
    main()