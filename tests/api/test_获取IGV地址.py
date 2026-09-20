import pytest
import allure


@allure.feature("API自动化")
class TestApi:
    @allure.story("获取IGV地址")
    def test_family_exoncnv(self, login_session, test_context):
        url = "http://test.sycamore.com/api/analysis/api/wgs/result/v1/family/exoncnv"
        params = {}
        json_data = {
            "sycId": "64678D8B9105414BABEE990EDD7AD96E",
            "itemStatus": 2
        }
        resp = login_session.post(url, params=params, json=json_data)
        test_context.capture(
            request={"url": url, "params": params, "payload": json_data},
            response=resp.json() if resp.text else ""
        )
        assert resp.status_code == 200