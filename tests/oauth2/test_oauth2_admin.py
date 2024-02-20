import pytest
from collections.abc import Set
from unittest.mock import patch
from regtech_api_commons.oauth2.config import KeycloakSettings
from regtech_api_commons.oauth2.oauth2_admin import OAuth2Admin
import jose.jwt
from keycloak import exceptions as kce


kc_settings = KeycloakSettings()
oauth2_admin = OAuth2Admin(kc_settings)


def test_get_claims():
    token = "Test Token"

    with patch.object(oauth2_admin, "_get_keys", return_value="secret"):
        claims = {
            "token": token,
            "iss": kc_settings.kc_realm_url.unicode_string(),
            "audience": kc_settings.auth_client,
            "options": kc_settings.jwt_opts,
        }

        encoded = jose.jwt.encode(claims=claims, key=oauth2_admin._get_keys(), algorithm="HS256")

        expected_result = jose.jwt.decode(
            token=encoded,
            key=oauth2_admin._get_keys(),
            issuer=kc_settings.kc_realm_url.unicode_string(),
            audience=kc_settings.auth_client,
            options=kc_settings.jwt_opts,
        )

        actual_result = oauth2_admin.get_claims(encoded)
        assert actual_result == expected_result


def test_update_user_passed(mocker):

    mock_update_user = mocker.patch("keycloak.KeycloakAdmin.update_user")
    mock_update_user.return_value = None

    res = oauth2_admin.update_user(user_id="test-user-id", payload={"Name": "Test"})
    assert res is None

    mock_get_user = mocker.patch("keycloak.KeycloakAdmin.get_user")
    mock_get_user.return_value = {"Name": "Test"}

    user = oauth2_admin._admin.get_user(user_id="test-user-id")
    assert user["Name"] == "Test"


def test_upsert_group(mocker):
    lei = "TESTLEI"
    name = "Test Name"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei, "Name": name}

    mock_update_group = mocker.patch("keycloak.KeycloakAdmin.update_group")
    mock_update_group.return_value = lei

    result = oauth2_admin.upsert_group(lei=lei, name=name)
    assert result == lei


def test_get_group(mocker):
    lei = "TESTLEI"
    name = "Test Name"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei, "Name": name}

    result = oauth2_admin.get_group(lei)
    assert result["Name"] == name


def test_assocaite_to_group(mocker):
    user_id = "test-id"
    group_id = "group-id"

    mock_group_user_add = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_group_user_add.return_value = None

    result = oauth2_admin.associate_to_group(user_id=user_id, group_id=group_id)
    assert result is None


def test_assocaite_to_lei(mocker):
    user_id = "test-id"
    lei = "TESTLEI"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei}

    mock_associate_to_group = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_associate_to_group.return_value = None

    result = oauth2_admin.associate_to_lei(user_id=user_id, lei=lei)
    assert result is None


def test_assocaite_to_leis(mocker):
    user_id = ("test-id",)
    leis = Set["TESTLEI1", "TESTLEI2", "TESTLEI3"]  # noqa: F821

    for lei in leis:

        mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
        mock_get_group.return_value = {"id": lei}

    mock_associate_to_group = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_associate_to_group.return_value = None

    result = oauth2_admin.associate_to_leis(user_id=user_id, leis=leis)
    assert result is None
