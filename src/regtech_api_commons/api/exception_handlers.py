import logging
from starlette.responses import JSONResponse
from starlette.requests import Request

from regtech_api_commons.api.exceptions import RegTechHttpException

log = logging.getLogger(__name__)


async def regtech_http_exception_handler(request: Request, exception: RegTechHttpException) -> JSONResponse:
    log.error(exception, exc_info=True, stack_info=True)
    return JSONResponse(
        status_code=exception.status_code, content={"error_name": exception.name, "error_detail": exception.detail}
    )
