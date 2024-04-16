from http import HTTPStatus
import json
from typing import Dict

from fastapi import Request
from fastapi.exceptions import RequestValidationError
import pytest
from pytest_mock import MockerFixture
from regtech_api_commons.api.exception_handlers import (
    regtech_http_exception_handler,
    request_validation_error_handler,
    log as exception_logger,
)
from regtech_api_commons.api.exceptions import RegTechHttpException


@pytest.fixture
def mock_request(mocker: MockerFixture) -> Request:
    mock = mocker.patch("fastapi.Request")
    return mock.return_value


async def test_regtech_http_exception_handler(mocker: MockerFixture, mock_request: Request):
    error_log_spy = mocker.patch.object(exception_logger, "error")
    e = RegTechHttpException(HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail="test exception detail")
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert content["error_name"] == e.name
    assert content["error_detail"] == e.detail
    assert isinstance(content["error_detail"], str)
    error_log_spy.assert_called_with(e, exc_info=True, stack_info=True)


async def test_regtech_http_exception_handler_nested_detail(mock_request: Request):
    e = RegTechHttpException(HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail={"foo": "bar"})
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert isinstance(content["error_detail"], Dict)


async def test_request_validation_error_handler(mock_request: Request):
    errors = [{"error1": "test1"}, {"error2": "test2"}]
    rve = RequestValidationError(errors=errors)
    response = await request_validation_error_handler(mock_request, rve)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    content = json.loads(response.body)
    assert content["error_name"] == "Request Validation Failure"
    assert content["error_detail"] == errors
