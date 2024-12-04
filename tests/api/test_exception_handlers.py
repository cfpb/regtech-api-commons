from http import HTTPStatus
import json

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import pytest
from pytest_mock import MockerFixture
from regtech_api_commons.api.exception_handlers import (
    ERROR_NAME,
    ERROR_DETAIL,
    regtech_http_exception_handler,
    request_validation_error_handler,
    http_exception_handler,
    general_exception_handler,
    log as exception_logger,
)
from regtech_api_commons.api.exceptions import RegTechHttpException


@pytest.fixture
def mock_request(mocker: MockerFixture) -> Request:
    mock = mocker.patch("fastapi.Request")
    return mock.return_value


async def test_regtech_http_exception_handler(mocker: MockerFixture, mock_request: Request):
    exception_log_spy = mocker.patch.object(exception_logger, "exception")
    e = RegTechHttpException(HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail="test exception detail")
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert content[ERROR_NAME] == e.name
    assert content[ERROR_DETAIL] == e.detail
    assert isinstance(content["error_detail"], str)
    exception_log_spy.assert_called()


async def test_regtech_http_exception_handler_nested_detail(mock_request: Request):
    e = RegTechHttpException(HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail={"foo": "bar"})
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert content[ERROR_DETAIL] == str({"foo": "bar"})


async def test_regtech_http_exception_handler_show_raw_nested_detail(mock_request: Request):
    e = RegTechHttpException(
        HTTPStatus.INTERNAL_SERVER_ERROR, name="Test Exception", detail={"foo": "bar"}, show_raw_detail=True
    )
    response = await regtech_http_exception_handler(mock_request, e)
    assert response.status_code == e.status_code
    content = json.loads(response.body)
    assert content[ERROR_DETAIL] == {"foo": "bar"}


async def test_request_validation_error_handler(mock_request: Request):
    errors = [{"loc": "test1", "msg": "error1"}, {"loc": "test2", "msg": "error2"}]
    rve = RequestValidationError(errors=errors)
    response = await request_validation_error_handler(mock_request, rve)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    content = json.loads(response.body)
    assert content[ERROR_DETAIL] == str(rve.errors())


async def test_general_http_exception_handler(mock_request: Request):
    e = HTTPException(HTTPStatus.NOT_FOUND, {"error1": "test1"})
    response = await http_exception_handler(mock_request, e)
    content = json.loads(response.body)
    assert content[ERROR_NAME] == HTTPStatus.NOT_FOUND.phrase
    assert content[ERROR_DETAIL] == str({"error1": "test1"})


async def test_general_http_exception_handler_with_starlette_error(mock_request: Request):
    e = StarletteHTTPException(HTTPStatus.FORBIDDEN, "test error")
    response = await http_exception_handler(mock_request, e)
    content = json.loads(response.body)
    assert content[ERROR_NAME] == HTTPStatus.FORBIDDEN.phrase
    assert content[ERROR_DETAIL] == "test error"


async def test_general_exception_handler(mock_request: Request):
    e = RuntimeError("test runtime error")
    response = await general_exception_handler(mock_request, e)
    content = json.loads(response.body)
    assert content[ERROR_NAME] == HTTPStatus.INTERNAL_SERVER_ERROR.phrase
    assert content[ERROR_DETAIL] == "server error"
