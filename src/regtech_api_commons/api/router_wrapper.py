from typing import Any, Callable

from fastapi import APIRouter
from fastapi.types import DecoratedCallable


class Router(APIRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @self.get("/healthcheck")
        async def healthcheck():
            return "Service is up."

    def api_route(
        self, path: str, *, include_in_schema: bool = True, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        if path.endswith("/"):
            path = path[:-1]

        add_path = super().api_route(path, include_in_schema=include_in_schema, **kwargs)

        add_alt_path = super().api_route(f"{path}/", include_in_schema=False, **kwargs)

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            add_alt_path(func)
            return add_path(func)

        return decorator
