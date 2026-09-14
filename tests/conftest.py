import os
import pytest
import requests
from dotenv import load_dotenv

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