import pytest
import allure


@allure.feature("API自动化")
class TestApi:
    @allure.story("样本更新")
    def test_sample_update_notice(self, login_session, test_context):
        url = "http://sunburst-test.bgi.com/sapi/sunburst-lab/api/lab/sap/sampleUpdateNotice"
        params = {}
        json_data = [
            {
                "sampleNo": "23S04682440",
                "sjdId": "INSP240000022260",
                "itemCp": "000001",
                "productNo": "DX2177",
                "familyNo": ""
            }
        ]
        resp = login_session.post(url, params=params, json=json_data)
        test_context.capture(
            request={"url": url, "params": params, "payload": json_data},
            response=resp.json() if resp.text else ""
        )
        assert resp.status_code == 200