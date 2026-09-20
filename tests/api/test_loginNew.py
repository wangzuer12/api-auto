import pytest
import allure


@allure.feature("API自动化")
class TestApi:
    @allure.story("loginNew")
    def test_login_new(self, login_session, test_context):
        url = "https://sunburst-test.bgi.com/sapi/sys/login?username=wangzuer2&password=44e0be6ec5d1121bb00d3fb1dc2d7de4"
        params = {
            "username": "wangzuer2",
            "password": "44e0be6ec5d1121bb00d3fb1dc2d7de4"
        }
        json_data = {
            "username": "wangzuer2",
            "password": "44e0be6ec5d1121bb00d3fb1dc2d7de4"
        }
        resp = login_session.post(url, params=params, json=json_data)
        test_context.capture(
            request={"url": url, "params": params, "payload": json_data},
            response=resp.json() if resp.text else ""
        )
        assert resp.status_code == 200