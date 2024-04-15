from http import HTTPStatus
import json
from typing import Dict

from fastapi import Request
import pytest
from pytest_mock import MockerFixture
from regtech_api_commons.api.exception_handlers import regtech_http_exception_handler
from regtech_api_commons.api.exceptions import RegTechHttpException


@pytest.fixture
def mock_request(mocker: MockerFixture) -> Request:
    mock = mocker.patch("fastapi.Request")
    return mock.return_value


async def test_regtech_http_exception_handler(mock_request: Request):
    e = RegTechHttpException(HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail="test exception detail")
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert content["error_name"] == e.name
    assert content["error_detail"] == e.detail
    assert isinstance(content["error_detail"], str)


async def test_regtech_http_exception_handler_nested_detail(mock_request: Request):
    e = RegTechHttpException(HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail={"foo": "bar"})
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert isinstance(content["error_detail"], Dict)
