from fastapi.security import OAuth2AuthorizationCodeBearer
import pytest
from regtech_api_commons.models.auth import AuthenticatedUser
from regtech_api_commons.oauth2.oauth2_admin import OAuth2Admin
from regtech_api_commons.oauth2.oauth2_backend import BearerTokenAuthBackend
from starlette.authentication import AuthCredentials
from starlette.requests import HTTPConnection
from conftest import kc_settings


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=kc_settings.auth_url.unicode_string(), tokenUrl=kc_settings.token_url.unicode_string()
)
oauth2_admin = OAuth2Admin(kc_settings=kc_settings)

bearer_token = BearerTokenAuthBackend(oauth2_scheme, oauth2_admin)


def test_oauth2_extract_nested():

    token = "Test Token"

    claims = {
        "token": token,
        "iss": "http://localhost/",
        "audience": "",
        "options": {},
        "realm_access": {"roles": ["offline_access", "uma_authorization"]},
        "resource_access": {"account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}},
    }

    assert bearer_token.extract_nested(claims, "resource_access", "account", "roles") == [
        "manage-account",
        "manage-account-links",
        "view-profile",
    ]


@pytest.mark.asyncio
async def test_oauth2_authenticate(mocker):

    token = "Test Token"

    mock_token_bearer = mocker.patch("fastapi.security.OAuth2AuthorizationCodeBearer.__call__")

    async def return_token_bearer_value(val):
        return val

    mock_token_bearer.return_value = return_token_bearer_value(token)

    mock_get_claims = mocker.patch("regtech_api_commons.oauth2.oauth2_admin.OAuth2Admin.get_claims")
    claims = {
        "token": token,
        "iss": "http://localhost/",
        "audience": "",
        "options": {},
        "realm_access": {"roles": ["offline_access", "uma_authorization"]},
        "resource_access": {"account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}},
    }
    mock_get_claims.return_value = claims

    scope = {
        "method": "GET",
        "type": "http",
        "headers": [("host", "localhost"), ("accept", "application/json")],
    }

    response = await bearer_token.authenticate(HTTPConnection(scope=scope))

    assert (
        response[0].scopes
        == AuthCredentials(["manage-account", "manage-account-links", "view-profile", "authenticated"]).scopes
    )
    assert response[1] == AuthenticatedUser.from_claim(claims)
