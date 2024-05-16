from http import HTTPStatus
from typing import Tuple

import httpx
import pytest
from fastapi import Request
from fastapi.exceptions import HTTPException
from pytest_mock import MockerFixture
from starlette.authentication import AuthCredentials, UnauthenticatedUser, BaseUser

from regtech_api_commons.api.dependencies import (
    parse_leis,
    verify_institution_search,
    verify_lei,
    verify_user_lei_relation,
)
from regtech_api_commons.api.exceptions import RegTechHttpException
from regtech_api_commons.models.auth import AuthenticatedUser


@pytest.fixture
def normal_context() -> Tuple[AuthCredentials, AuthenticatedUser]:
    return AuthCredentials(scopes=["authenticated"]), AuthenticatedUser.from_claim(
        {
            "name": "test",
            "preferred_username": "test_user",
            "email": "test@local.host",
            "sub": "testuser123",
            "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
        }
    )


@pytest.fixture
def admin_context() -> Tuple[AuthCredentials, AuthenticatedUser]:
    return AuthCredentials(scopes=["query-groups", "manage-users", "authenticated"]), AuthenticatedUser.from_claim(
        {
            "name": "admin",
            "preferred_username": "admin_user",
            "email": "admin@local.host",
            "sub": "adminuser123",
        }
    )


@pytest.fixture
def unauthed_context() -> Tuple[AuthCredentials, BaseUser]:
    return AuthCredentials("unauthenticated"), UnauthenticatedUser()


def test_verify_lei_dependency_inactive(mocker: MockerFixture):
    mock_user_fi_service = mocker.patch("regtech_api_commons.api.dependencies.httpx.get")
    mock_user_fi_service.return_value = httpx.Response(200, json={"is_active": False})
    lei_check = verify_lei("test")
    with pytest.raises(HTTPException) as http_exc:
        request = Request(scope={"type": "http", "headers": [(b"authorization", b"123")]})
        lei_check(request=request, lei="1234567890ZXWVUTSR00")
    assert isinstance(http_exc.value, HTTPException)
    assert http_exc.value.status_code == 403
    assert http_exc.value.detail == "LEI 1234567890ZXWVUTSR00 is in an inactive state."


def test_verify_lei_dependency_active(mocker: MockerFixture):
    mock_user_fi_service = mocker.patch("regtech_api_commons.api.dependencies.httpx.get")
    mock_user_fi_service.return_value = httpx.Response(200, json={"is_active": True})
    lei_check = verify_lei("test")
    request = Request(scope={"type": "http", "headers": [(b"authorization", b"123")]})
    lei_check(request=request, lei="1234567890ZXWVUTSR00")


def test_verify_user_lei_relation_admin(admin_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = admin_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    verify_user_lei_relation(request, lei="TESTLEI123")


def test_verify_user_lei_relation_valid(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    verify_user_lei_relation(request, lei="TEST1LEI")


def test_verify_user_lei_relation_invalid(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_user_lei_relation(request, lei="TEST0LEI")
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN


def test_verify_user_lei_relation_unauthed(unauthed_context: Tuple[AuthCredentials, BaseUser]):
    auth, user = unauthed_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_user_lei_relation(request, lei="TESTLEI")
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN


def test_verify_user_lei_relation_no_param():
    request = Request(scope={"type": "http"})
    verify_user_lei_relation(request)


def test_verify_institution_search_leis_admin(admin_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = admin_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    verify_institution_search(request, leis=["TEST0LEI", "TEST1CHILDLEI"])


def test_verify_institution_search_domain_admin(admin_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = admin_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    verify_institution_search(request, domain="not_associated.domain")


def test_verify_institution_search_leis_valid(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    verify_institution_search(request, leis=["TEST1LEI", "TEST2CHILDLEI"])


def test_verify_institution_search_leis_invalid(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_institution_search(request, leis=["TEST0LEI", "TEST2CHILDLEI"])
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN


def test_verify_institution_search_domain_valid(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    verify_institution_search(request, leis=None, domain="local.host")


def test_verify_institution_search_domain_invalid(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_institution_search(request, leis=None, domain="not_associated.domain")
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN


def test_verify_institution_search_no_user_email(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    user.email = ""
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_institution_search(request, leis=None, domain="not_associated.domain")
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN


def test_verify_institution_search_no_param(normal_context: Tuple[AuthCredentials, AuthenticatedUser]):
    auth, user = normal_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_institution_search(request, leis=None)
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN
    assert excpt.detail == "Retrieving institutions without filter is forbidden."


def test_verify_institution_search_unauthed(unauthed_context: Tuple[AuthCredentials, BaseUser]):
    auth, user = unauthed_context
    request = Request(scope={"auth": auth, "user": user, "type": "http"})
    with pytest.raises(HTTPException) as e:
        verify_institution_search(request, leis=None)
    excpt = e.value
    assert isinstance(excpt, RegTechHttpException)
    assert excpt.status_code == HTTPStatus.FORBIDDEN


def test_parse_leis():
    assert parse_leis(["lei1,lei2"]) == ["lei1", "lei2"]
    assert parse_leis(["lei1,lei2", "lei3,lei4"]) == ["lei1", "lei2", "lei3", "lei4"]
    assert parse_leis([]) is None
    assert parse_leis(None) is None
