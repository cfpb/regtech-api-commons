from starlette.responses import JSONResponse
from starlette.requests import Request

from regtech_api_commons.api.exceptions import RegTechHttpException


async def regtech_http_exception_handler(request: Request, exception: RegTechHttpException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code, content={"error_name": exception.name, "error_detail": exception.detail}
    )
