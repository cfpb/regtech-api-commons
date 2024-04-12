from starlette.exceptions import HTTPException as StarletteHTTPException

class RegTechHttpException(StarletteHTTPException):
    name: str | None

    def __init__(self, status_code: int, name: str | None = None, detail: str | None = None, headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code, detail, headers)
        self.name = name
