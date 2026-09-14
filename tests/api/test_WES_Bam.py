import time
import allure
import pytest


@allure.feature("WES-Bam")
class TestWesBam:
    """WES-Bam 接口测试：POST /api/sycamore-wes/sunburst/v1/single/bamInfo"""

    @allure.story("正向用例-查询Bam信息成功")
    @pytest.mark.parametrize("payload", [
        {"sycId": "754927CEEA594CB5A4F88C589514D676", "itemStatus": 2}
    ])
    def test_wes_bam_success(self, api_session, base_url, payload):
        url = "http://test.sycamore.com/api/sycamore-wes/sunburst/v1/single/bamInfo"
        with allure.step("准备请求数据"):
            allure.attach(str(payload), "请求payload", allure.attachment_type.TEXT)
        with allure.step("发送POST请求"):
            start = time.time()
            resp = api_session.post(url, json=payload)
            elapsed = time.time() - start
        with allure.step("校验响应状态码与响应时间"):
            assert resp.status_code == 200, f"状态码异常: {resp.status_code}"
            assert elapsed < 3, f"响应时间过长: {elapsed:.2f}s"
        with allure.step("校验业务返回"):
            body = resp.json()
            allure.attach(str(body), "响应body", allure.attachment_type.JSON)
            assert body.get("success") is True, f"业务success异常: {body.get('success')}, retInfo: {body.get('retInfo')}, body: {body}"
            assert body.get("retCode") == 0, f"业务retCode异常: {body.get('retCode')}, retInfo: {body.get('retInfo')}, body: {body}"
            assert body.get("result") is not None, f"业务result为空: {body}"
        with allure.step("校验关键数据字段存在性"):
            result = body.get("result")
            assert result is not None, f"result为空: {body}"

    @allure.story("异常用例-缺少必填参数sycId")
    @pytest.mark.parametrize("payload", [
        {"itemStatus": 2}
    ])
    def test_wes_bam_missing_sycid(self, api_session, base_url, payload):
        url = "http://test.sycamore.com/api/sycamore-wes/sunburst/v1/single/bamInfo"
        with allure.step("准备异常请求数据"):
            allure.attach(str(payload), "请求payload", allure.attachment_type.TEXT)
        with allure.step("发送POST请求"):
            start = time.time()
            resp = api_session.post(url, json=payload)
            elapsed = time.time() - start
        with allure.step("校验响应状态码与响应时间"):
            assert resp.status_code in (200, 400, 422), f"状态码异常: {resp.status_code}"
            assert elapsed < 3, f"响应时间过长: {elapsed:.2f}s"
        with allure.step("校验业务异常返回"):
            body = resp.json()
            allure.attach(str(body), "响应body", allure.attachment_type.JSON)
            assert (
                body.get("success") is False
                or body.get("retCode") != 0
                or body.get("retInfo") is not None
            ), f"异常用例未返回预期错误信息: {body}"

    @allure.story("异常用例-错误参数itemStatus")
    @pytest.mark.parametrize("payload", [
        {"sycId": "754927CEEA594CB5A4F88C589514D676", "itemStatus": -1}
    ])
    def test_wes_bam_invalid_itemstatus(self, api_session, base_url, payload):
        url = "http://test.sycamore.com/api/sycamore-wes/sunburst/v1/single/bamInfo"
        with allure.step("准备异常请求数据"):
            allure.attach(str(payload), "请求payload", allure.attachment_type.TEXT)
        with allure.step("发送POST请求"):
            start = time.time()
            resp = api_session.post(url, json=payload)
            elapsed = time.time() - start
        with allure.step("校验响应状态码与响应时间"):
            assert resp.status_code in (200, 400, 422), f"状态码异常: {resp.status_code}"
            assert elapsed < 3, f"响应时间过长: {elapsed:.2f}s"
        with allure.step("校验业务异常返回"):
            body = resp.json()
            allure.attach(str(body), "响应body", allure.attachment_type.JSON)
            assert (
                body.get("success") is False
                or body.get("retCode") != 0
                or body.get("retInfo") is not None
            ), f"异常用例未返回预期错误信息: {body}"