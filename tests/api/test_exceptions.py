from http import HTTPStatus
import pytest

from regtech_api_commons.api.exceptions import RegTechHttpException


async def test_regtech_http_exception():
    with pytest.raises(RegTechHttpException) as e:
        raise RegTechHttpException(
            HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail="this is a test exception"
        )
    assert e.value.name == "Test Exception"
    assert e.value.detail == "this is a test exception"


async def test_regtech_http_exception_with_nested_detail():
    with pytest.raises(RegTechHttpException) as e:
        raise RegTechHttpException(
            HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Nested Detail Exception", detail={"foo": "bar"}
        )
    assert e.value.name == "Test Nested Detail Exception"
    assert e.value.detail == {"foo": "bar"}
