"""
统一 LLM 客户端封装
- 从 .env 读取 DEEPSEEK_API_KEY
- 提供 chat() / chat_with_reasoner() / extract_code()
- 所有 AI 调用走这里，不再到处 new OpenAI()
"""
import os
from pathlib import Path
from openai import OpenAI

# 项目根目录
ROOT = Path(__file__).resolve().parents[2]


def _load_env():
    """手动加载 .env（不依赖 python-dotenv，轻量）"""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


_load_env()


def get_client() -> OpenAI:
    """获取配置好的 OpenAI 客户端（DeepSeek 兼容）"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY 未设置！\n"
            "请确认：\n"
            "1. 项目根目录有 .env 文件\n"
            "2. .env 里有 DEEPSEEK_API_KEY=sk-xxx\n"
            "3. .env 没有被 git 误提交"
        )

    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


def chat(
    prompt: str,
    system: str = "你是接口自动化测试专家，只输出可运行代码或清晰分析。",
    model: str = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> str:
    """
    调用 DeepSeek 聊天接口

    Args:
        prompt: 用户 prompt
        system: 系统角色设定
        model: 模型名，默认 deepseek-chat
        temperature: 创造性（0=确定性）
        max_tokens: 最大输出长度

    Returns:
        LLM 返回的文本内容
    """
    model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    client = get_client()

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = resp.choices[0].message.content or ""
    return content.strip()


def chat_with_reasoner(prompt: str) -> str:
    """使用推理模型（适合失败分析、复杂接口分析）"""
    return chat(
        prompt=prompt,
        system="你是接口自动化测试失败分析专家，结合接口、请求、响应、断言和报错定位原因。",
        model="deepseek-reasoner",
        temperature=0.0,
        max_tokens=8192,
    )


def extract_code(text: str, lang: str = "python") -> str:
    """
    清洗 LLM 返回的代码块标记

    输入: ```python\ncode\n``` 或 ```\ncode\n```
    输出: 纯代码
    """
    text = text.strip()
    fence = f"```{lang}"
    if text.startswith(fence):
        text = text[len(fence):]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()