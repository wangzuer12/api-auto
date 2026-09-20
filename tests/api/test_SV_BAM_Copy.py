import pytest
import allure


@allure.feature("API自动化")
class TestApi:
    @allure.story("SV-BAM Copy")
    def test_sv_bam_copy(self, login_session, test_context):
        url = "http://test.sycamore.com/api/analysis/api/wgs/result/v1/single/bamInfo"
        params = {}
        json_data = {
            "sycId": "73E5E598BC9A4912B6CB777518858EF0",
            "itemStatus": 2
        }
        resp = login_session.post(url, params=params, json=json_data)
        test_context.capture(
            request={"url": url, "params": params, "payload": json_data},
            response=resp.json() if resp.text else ""
        )
        assert resp.status_code == 200