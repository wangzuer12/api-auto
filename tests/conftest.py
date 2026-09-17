import os
import json
import pytest
import requests
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path


load_dotenv()


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("API_BASE_URL", "http://test.sycamore.com")


@pytest.fixture(scope="session")
def api_session():
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    token = os.getenv("API_TOKEN")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
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