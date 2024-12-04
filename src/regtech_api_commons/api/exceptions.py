from typing import Any, Dict
from fastapi import HTTPException


class RegTechHttpException(HTTPException):
    name: str | None
    show_raw_detail: bool

    def __init__(
        self,
        status_code: int,
        name: str | None = None,
        detail: Any = None,
        headers: Dict[str, str] | None = None,
        show_raw_detail: bool = False,
    ) -> None:
        super().__init__(status_code, detail, headers)
        self.name = name
        self.show_raw_detail = show_raw_detail
