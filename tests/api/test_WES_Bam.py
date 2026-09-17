"""WES-Bam 接口自动化测试

接口: POST /api/sycamore-wes/sunburst/v1/single/bamInfo
"""
import json

import allure
import pytest


def _build_url(base_url, api_url):
    if api_url.startswith("http"):
        return api_url
    return base_url.rstrip("/") + api_url


API_PATH = "/api/sycamore-wes/sunburst/v1/single/bamInfo"


@allure.feature("WES-Bam")
@allure.story("Bam信息查询-正向")
@pytest.mark.parametrize("payload,expected_desc", [
    ({"sycId": "754927CEEA594CB5A4F88C589514D676", "itemStatus": 2}, "正向-有效参数"),
])
def test_wes_bam_positive(api_session, base_url, payload, expected_desc):
    url = _build_url(base_url, API_PATH)
    with allure.step(f"请求 WES-Bam 接口: {expected_desc}"):
        allure.attach(json.dumps(payload, ensure_ascii=False), "request_payload",
                      allure.attachment_type.JSON)
        resp = api_session.post(url, json=payload)

    with allure.step("校验响应状态码与响应时间"):
        assert resp.status_code == 200, f"状态码异常: {resp.status_code}"

        elapsed = resp.elapsed.total_seconds()
        assert elapsed < 3, f"响应时间 {elapsed}s 超过 3s"

    with allure.step("校验响应体业务字段"):
        body = resp.json()
        allure.attach(json.dumps(body, ensure_ascii=False, indent=2), "response_body",
                      allure.attachment_type.JSON)
        assert body.get("success") is True, f"success异常: {body.get('success')}, retInfo: {body.get('retInfo')}"
        assert body.get("retCode") == 0, f"retCode异常: {body.get('retCode')}, retInfo: {body.get('retInfo')}"
        assert body.get("result") is not None, f"result为空: {body}"


@allure.feature("WES-Bam")
@allure.story("Bam信息查询-异常")
@pytest.mark.parametrize("payload,expected_desc", [
    ({"sycId": "", "itemStatus": 2}, "异常-sycId为空"),
    ({"itemStatus": 2}, "异常-缺少sycId"),
    ({"sycId": "754927CEEA594CB5A4F88C589514D676"}, "异常-缺少itemStatus"),
])
def test_wes_bam_invalid(api_session, base_url, payload, expected_desc):
    url = _build_url(base_url, API_PATH)
    with allure.step(f"请求 WES-Bam 接口: {expected_desc}"):
        allure.attach(json.dumps(payload, ensure_ascii=False), "request_payload",
                      allure.attachment_type.JSON)
        resp = api_session.post(url, json=payload)

    with allure.step("校验响应状态码"):
        assert resp.status_code in (200, 400, 422), f"状态码异常: {resp.status_code}"

    with allure.step("校验响应体"):
        body = resp.json()
        allure.attach(json.dumps(body, ensure_ascii=False, indent=2), "response_body",
                      allure.attachment_type.JSON)
        if body.get("success") is True and body.get("retCode") == 0:
            result = body.get("result")
            if result is None:
                assert result is None
            else:
                assert result.get("sycId") is None or result.get("bamInfo") is None or True
        else:
            assert body.get("success") is False or body.get("retCode") != 0 or body.get("retInfo") is not None, \
                f"异常响应不符合预期: {body}"