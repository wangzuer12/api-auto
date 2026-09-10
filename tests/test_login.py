import requests
import allure

BASE = "https://jsonplaceholder.typicode.com"

@allure.feature("登录相关")
def test_get_user():
    r = requests.get(f"{BASE}/users/1", timeout=10)
    assert r.status_code == 200
    assert r.json()["id"] == 1

@allure.feature("登录相关")
def test_get_user_not_found():
    r = requests.get(f"{BASE}/users/9999", timeout=10)
    assert r.status_code == 404