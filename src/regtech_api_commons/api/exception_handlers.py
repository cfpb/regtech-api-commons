from http import HTTPStatus
import logging
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.requests import Request

from regtech_api_commons.api.exceptions import RegTechHttpException

log = logging.getLogger(__name__)


async def regtech_http_exception_handler(request: Request, exception: RegTechHttpException) -> JSONResponse:
    log.error(exception, exc_info=True, stack_info=True)
    return JSONResponse(
        status_code=exception.status_code, content={"error_name": exception.name, "error_detail": exception.detail}
    )


async def request_validation_error_handler(request: Request, exception: RequestValidationError) -> JSONResponse:
    log.warn(exception, exc_info=True, stack_info=True)
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"error_name": "Request Validation Failure", "error_detail": exception.errors()},
    )
