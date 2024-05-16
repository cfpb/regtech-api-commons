import os
from http import HTTPStatus
from itertools import chain
from typing import List

import httpx
from fastapi import Depends, Query, Request
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


def verify_user_lei_relation(request: Request, lei: str | None = None) -> None:
    if lei:
        user: AuthenticatedUser = request.user
        auth: AuthCredentials = request.auth
        detail = "Unauthenticated Request Forbidden."
        if user.is_authenticated:
            if is_admin(auth) or lei in user.institutions:
                return
            else:
                detail = f"LEI {lei} is not associated with the user."
        raise RegTechHttpException(
            status_code=HTTPStatus.FORBIDDEN,
            name="Request Forbidden",
            detail=detail,
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


def parse_leis(leis: List[str] | None = Query(None)) -> List[str] | None:
    """
    Parses leis from list of one or multiple strings to a list of
    multiple distinct lei strings.
    Returns empty list when nothing is passed in
    Ex1: ['lei1,lei2'] -> ['lei1', 'lei2']
    Ex2: ['lei1,lei2', 'lei3,lei4'] -> ['lei1','lei2','lei3','lei4']
    """

    if leis:
        return list(chain.from_iterable([x.split(",") for x in leis]))
    else:
        return None


def verify_institution_search(
    request: Request, leis: List[str] | None = Depends(parse_leis), domain: str | None = None
) -> None:
    user: AuthenticatedUser = request.user
    auth: AuthCredentials = request.auth
    detail = "Unauthenticated Request Forbidden."
    if user.is_authenticated:
        if is_admin(auth):
            return
        if leis:
            verify_lei_search(user, leis)
            return
        elif domain:
            verify_domain_search(user, domain)
            return
        elif not leis and not domain:
            detail = "Retrieving institutions without filter is forbidden."
    raise RegTechHttpException(
        HTTPStatus.FORBIDDEN,
        name="Request Forbidden",
        detail=detail,
    )
