import os
from http import HTTPStatus
from typing import List

import httpx
from fastapi import Request
from starlette.authentication import AuthCredentials

from regtech_api_commons.api.exceptions import RegTechHttpException
from regtech_api_commons.models.auth import AuthenticatedUser


def verify_lei(inst_api_url: str):
    def lei_active_check(request: Request, lei: str) -> None:
        res = httpx.get(inst_api_url + lei, headers={"authorization": request.headers["authorization"]})
        lei_obj = res.json()
        if not lei_obj["is_active"]:
            raise RegTechHttpException(
                status_code=HTTPStatus.FORBIDDEN, name="Request Forbidden", detail=f"LEI {lei} is in an inactive state."
            )

    return lei_active_check


def verify_user_lei_relation(request: Request, *args, **kwargs) -> None:
    if lei := kwargs.get("lei"):
        user: AuthenticatedUser = request.user
        auth: AuthCredentials = request.auth
        if not is_admin(auth):
            if lei not in user.institutions:
                raise RegTechHttpException(
                    status_code=HTTPStatus.FORBIDDEN,
                    name="Request Forbidden",
                    detail=f"LEI {lei} is not associated with the user.",
                )


def is_admin(auth: AuthCredentials):
    return all(scope in auth.scopes for scope in os.getenv("ADMIN_SCOPES", "query-groups,manage-users").split(","))


def get_email_domain(email: str) -> str | None:
    if email:
        return email.split("@")[-1]
    return None


def verify_lei_search(user: AuthenticatedUser, leis: List[str]) -> None:
    if not set(filter(len, leis)).issubset(set(filter(len, user.institutions))):
        raise RegTechHttpException(
            HTTPStatus.FORBIDDEN,
            name="Request Forbidden",
            detail=f"Institutions query with LEIs ({leis}) not associated with user is forbidden.",
        )


def verify_domain_search(user: AuthenticatedUser, domain: str) -> None:
    if domain != get_email_domain(user.email):
        raise RegTechHttpException(
            HTTPStatus.FORBIDDEN,
            name="Request Forbidden",
            detail=f"Institutions query with domain ({domain}) not associated with user is forbidden.",
        )


def verify_institution_search(request: Request, *args, **kwargs) -> None:
    user: AuthenticatedUser = request.user
    auth: AuthCredentials = request.auth
    if not is_admin(auth):
        leis = kwargs.get("leis")
        domain = kwargs.get("domain")
        if leis:
            verify_lei_search(user, leis)
        elif domain:
            verify_domain_search(user, domain)
        elif not leis and not domain:
            raise RegTechHttpException(
                HTTPStatus.FORBIDDEN,
                name="Request Forbidden",
                detail="Retrieving institutions without filter is forbidden.",
            )
