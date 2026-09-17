"""
DeepSeek API 连通性验证（使用统一 LLM 封装）
"""
import sys
from pathlib import Path

# 把项目根目录加入 path，方便导入 scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.ai_gen.llm_client import chat, extract_code


def main():
    print("=" * 50)
    print("DeepSeek API 连通性验证")
    print("=" * 50)

    try:
        raw = chat(
            prompt="用 pytest+requests 写一个 GET /health 的冒烟测试，只输出代码",
            system="你是接口自动化测试专家，只输出 Python 代码。",
        )
        print("\n--- LLM 原始返回 ---")
        print(raw)

        code = extract_code(raw)
        print("\n--- 清洗后代码 ---")
        print(code)

        print("\n✅ 调用成功！LLM 封装正常工作。")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()