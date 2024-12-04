from http import HTTPStatus
import logging
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.exceptions import HTTPException

from regtech_api_commons.api.exceptions import RegTechHttpException

log = logging.getLogger(__name__)

ERROR_NAME = "error_name"
ERROR_DETAIL = "error_detail"


async def regtech_http_exception_handler(request: Request, exception: RegTechHttpException) -> JSONResponse:
    log.exception("Handling RegTechHttpException.")
    detail = exception.detail if exception.show_raw_detail else str(exception.detail)
    return JSONResponse(
        status_code=exception.status_code,
        content={ERROR_NAME: exception.name, ERROR_DETAIL: detail},
    )


async def request_validation_error_handler(request: Request, exception: RequestValidationError) -> JSONResponse:
    log.warning("Handling RequestValidationError.", exc_info=True)
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={ERROR_NAME: "Request Validation Failure", ERROR_DETAIL: str(exception.errors())},
    )


async def http_exception_handler(request: Request, exception: HTTPException) -> JSONResponse:
    log.exception("Handling HTTPException.")
    status = HTTPStatus(exception.status_code)
    return JSONResponse(
        status_code=exception.status_code,
        content={ERROR_NAME: status.phrase, ERROR_DETAIL: str(exception.detail)},
    )


async def general_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    log.exception("Handling General Exception.")
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={ERROR_NAME: HTTPStatus.INTERNAL_SERVER_ERROR.phrase, ERROR_DETAIL: "server error"},
    )
