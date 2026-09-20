import os
import json
import pytest
import requests
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

load_dotenv()

# ============新增 env_config fixture===========
@pytest.fixture(scope="session")
def env_config():
    """多服务域名配置，login和bam使用不同base地址"""
    return {
        "login": os.getenv("API_LOGIN_URL", "https://sunburst-test.bgi.com"),
        "bam": os.getenv("API_BAM_URL", "http://test.sycamore.com"),
    }


@pytest.fixture(scope="session")
def api_session():
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    # 删除旧逻辑：不再读取API_TOKEN，token由login_session登录后自动注入
    yield s
    s.close()


# ========== 失败自动收集 ==========
FAILURE_JSON = Path(__file__).resolve().parents[1] / "reports" / "failures.json"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.outcome != "failed":
        return

    test_context = getattr(item, "_test_context", {})

    failures = []
    if FAILURE_JSON.exists():
        try:
            failures = json.loads(FAILURE_JSON.read_text(encoding="utf-8"))
        except Exception:
            failures = []

    failure_entry = {
        "test_name": item.nodeid,
        "test_function": item.name,
        "duration": round(report.duration, 3),
        "timestamp": datetime.now().isoformat(),
        "error_message": str(report.longrepr) if report.longrepr else "",
        "traceback": str(report.longrepr) if report.longrepr else "",
        "request": test_context.get("request", {}),
        "response": test_context.get("response", {}),
        "payload": test_context.get("payload", {}),
        "expected": test_context.get("expected", {}),
    }

    failures.append(failure_entry)
    FAILURE_JSON.parent.mkdir(parents=True, exist_ok=True)
    FAILURE_JSON.write_text(
        json.dumps(failures, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@pytest.fixture
def test_context(request):
    """测试上下文收集器，供测试函数挂 request/response"""
    class TestContext:
        def __init__(self, item):
            self._item = item

        def capture(self, **kwargs):
            if not hasattr(self._item, "_test_context"):
                self._item._test_context = {}
            self._item._test_context.update(kwargs)

    return TestContext(request.node)


@pytest.fixture(scope="session")
def login_session(api_session, env_config):
    login_base = env_config["login"]
    login_url = login_base.rstrip("/") + "/sapi/sys/login"
    # 👉 Query参数，username补全末尾2
    login_params = {
        "username": "wangzuer2",
        "password": "44e0be6ec5d1121bb00d3fb1dc2d7de4"
    }
    # 登录前临时清空header，避免请求带旧token
    old_auth = api_session.headers.pop("Authorization", None)
    # POST请求，参数放在params（url查询参数，body为空，和Postman保持一致）
    resp = api_session.post(login_url, params=login_params)
    print(f"【登录debug】status={resp.status_code}, text={resp.text}")

    if resp.text and resp.text.strip():
        res = resp.json()
    else:
        # 异常时恢复header
        if old_auth:
            api_session.headers["Authorization"] = old_auth
        raise Exception("登录接口返回空")

    if res.get("retCode") != 0:
        # 恢复旧header再抛异常
        if old_auth:
            api_session.headers["Authorization"] = old_auth
        raise Exception(f"登录业务失败：{res}")
    token = res["token"]
    api_session.headers["Authorization"] = f"Bearer {token}"
    return api_session
