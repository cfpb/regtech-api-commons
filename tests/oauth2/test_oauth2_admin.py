from keycloak import KeycloakError
from pytest_mock import MockerFixture
import pytest
from collections.abc import Set
from unittest.mock import Mock
from regtech_api_commons.api.exceptions import RegTechHttpException
from regtech_api_commons.models.auth import RegTechUser
from regtech_api_commons.oauth2.oauth2_admin import KeycloakSettings, OAuth2Admin
from regtech_regex.regex_config import RegexConfigs

import base64
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

kc_settings = KeycloakSettings(
    **{
        "kc_url": "http://localhost",
        "kc_realm": "",
        "kc_admin_client_id": "",
        "kc_admin_client_secret": "",
        "kc_realm_url": "http://localhost",
        "auth_url": "http://localhost",
        "token_url": "http://localhost",
        "certs_url": "http://localhost",
        "auth_client": "regtech-client",
    }
)
oauth2_admin = OAuth2Admin(kc_settings)


def test_get_claims(mocker):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    token = jwt.encode(
        {
            "sub": "test-user",
            "iss": "http://localhost/",
            "aud": kc_settings.auth_client,
            "options": kc_settings._jwt_opts,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )

    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    jwk = {
        "kty": "RSA",
        "kid": "test-kid",
        "use": "sig",
        "n": base64.urlsafe_b64encode(
            public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big")
        ).decode("utf-8"),
        "e": base64.urlsafe_b64encode(
            public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big")
        ).decode("utf-8"),
    }
    keys = {"keys": [jwk]}

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.content = "CONTENT"
    mock_resp.json = Mock(return_value=keys)

    mock_request = mocker.patch("requests.get", return_value=mock_resp)
    actual_result = oauth2_admin.get_claims(token)

    mock_request.assert_called_with(kc_settings.certs_url)
    print(f"{actual_result}")
    assert actual_result["iss"] == "http://localhost/"
    assert actual_result["aud"] == kc_settings.auth_client


def test_update_user(mocker: MockerFixture):
    mock_update_user = mocker.patch("keycloak.KeycloakAdmin.update_user")
    user_id = "test-user-id"
    payload = {"Name": "Test"}

    oauth2_admin.update_user(user_id=user_id, payload=payload)
    mock_update_user.assert_called_once_with(user_id, payload)


def test_update_user_failure(mocker: MockerFixture):
    mock_update_user = mocker.patch("keycloak.KeycloakAdmin.update_user")
    kce_code = 500
    mock_update_user.side_effect = KeycloakError("test", kce_code)
    log_mock = mocker.patch("regtech_api_commons.oauth2.oauth2_admin.log")
    with pytest.raises(RegTechHttpException) as e:
        oauth2_admin.update_user("test", {"foo": "bar"})
    log_mock.exception.assert_called()
    assert e.value.status_code == kce_code


def test_upsert_group_new(mocker: MockerFixture):
    lei = "TESTLEI"
    name = "Test Name"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = None

    mock_update_group = mocker.patch("keycloak.KeycloakAdmin.create_group")
    mock_update_group.return_value = lei

    result = oauth2_admin.upsert_group(lei=lei, name=name)
    assert result == lei

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"error": "Group path does not exist"}

    result = oauth2_admin.upsert_group(lei=lei, name=name)
    assert result == lei


def test_upsert_group_existing(mocker: MockerFixture):
    lei = "TESTLEI"
    name = "Test Name"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei, "Name": name}

    mock_update_group = mocker.patch("keycloak.KeycloakAdmin.update_group")
    mock_update_group.return_value = lei

    result = oauth2_admin.upsert_group(lei=lei, name=name)
    assert result == lei


def test_upsert_group_failure(mocker: MockerFixture):
    lei = "TESTLEI"
    name = "Test Name"
    kce_code = 500

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei, "Name": name}

    mock_update_group = mocker.patch("keycloak.KeycloakAdmin.update_group")
    mock_update_group.side_effect = KeycloakError("test", response_code=kce_code)

    log_mock = mocker.patch("regtech_api_commons.oauth2.oauth2_admin.log")

    with pytest.raises(RegTechHttpException) as e:
        oauth2_admin.upsert_group(lei=lei, name=name)
    log_mock.exception.assert_called()
    assert e.value.status_code == kce_code


def test_get_user(mocker: MockerFixture):
    mock_get_user = mocker.patch("keycloak.KeycloakAdmin.get_user")
    mock_get_user.return_value = {
        "email": "test@local.host",
        "firstName": "test",
        "id": "testuser123",
        "lastName": "user",
        "username": "user1",
    }
    mock_get_groups = mocker.patch("keycloak.KeycloakAdmin.get_user_groups")
    mock_get_groups.return_value = [
        {"id": "test-id-1", "name": "TEST1LEI", "path": "/TEST1LEI"},
        {"id": "test-id-2", "name": "TEST2CHILDLEI", "path": "/TEST2LEI/TEST2CHILDLEI"},
    ]
    regtech_user = oauth2_admin.get_user("testuser123")
    mock_get_user.assert_called_with("testuser123")
    mock_get_groups.assert_called_with("testuser123")
    assert regtech_user.email == "test@local.host"
    assert regtech_user.institutions == ["TEST1LEI", "TEST2CHILDLEI"]
    assert isinstance(regtech_user, RegTechUser)


def test_get_group(mocker):
    lei = "TESTLEI"
    name = "Test Name"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei, "Name": name}

    result = oauth2_admin.get_group(lei)
    assert result["Name"] == name


def test_associate_to_group(mocker: MockerFixture):
    user_id = "test-id"
    group_id = "group-id"

    mock_group_user_add = mocker.patch("keycloak.KeycloakAdmin.group_user_add")

    oauth2_admin.associate_to_group(user_id=user_id, group_id=group_id)
    mock_group_user_add.assert_called_with(user_id, group_id)


def test_associate_to_group_failure(mocker: MockerFixture):
    user_id = "test-id"
    group_id = "group-id"
    kce_code = 500

    mock_group_user_add = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_group_user_add.side_effect = KeycloakError("test", response_code=kce_code)

    log_mock = mocker.patch("regtech_api_commons.oauth2.oauth2_admin.log")

    with pytest.raises(RegTechHttpException) as e:
        oauth2_admin.associate_to_group(user_id=user_id, group_id=group_id)

    log_mock.exception.assert_called()
    assert e.value.status_code == kce_code


def test_associate_to_lei(mocker):
    user_id = "test-id"
    lei = "123456789TESTBANK123"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei}

    mock_associate_to_group = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_associate_to_group.return_value = None

    result = oauth2_admin.associate_to_lei(user_id=user_id, lei=lei)
    assert result is None


def test_associate_to_lei_invalid():
    regex_configs = RegexConfigs.instance()
    with pytest.raises(Exception) as e:
        user_id = "test-id"
        lei = "TESTLEI"
        oauth2_admin.associate_to_lei(user_id=user_id, lei=lei)
    assert f"Invalid LEI TESTLEI. {regex_configs.lei.error_text}" in e.value.args


def test_associate_to_leis(mocker):
    user_id = ("test-id",)
    leis = Set["123456789TESTBANK123", "123456789TESTBANK234", "123456789TESTBANK345"]  # noqa: F722

    associate_to_lei_mock = mocker.patch(
        "regtech_api_commons.oauth2.oauth2_admin.OAuth2Admin.associate_to_lei", return_value=None
    )

    oauth2_admin.associate_to_leis(user_id, leis)

    for lei in leis:
        associate_to_lei_mock.assert_called_with(user_id, lei)


def test_delete_group(mocker):
    lei = "TESTLEI"
    kce_code = 500
    group_id = "test-id"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": group_id, "Name": lei}

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.delete_group")
    mock_get_group.return_value = None

    result = oauth2_admin.delete_group(mock_get_group["id"])
    assert result is None

    mock_get_group.side_effect = KeycloakError("test", response_code=kce_code)
    log_mock = mocker.patch("regtech_api_commons.oauth2.oauth2_admin.log")

    with pytest.raises(RegTechHttpException) as e:
        oauth2_admin.delete_group(lei=lei)
    log_mock.exception.assert_called()
    assert e.value.status_code == kce_code
