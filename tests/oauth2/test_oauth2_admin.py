from pytest_mock import MockerFixture
from collections.abc import Set
from unittest.mock import Mock
from regtech_api_commons.models.auth import RegTechUser
from regtech_api_commons.oauth2.oauth2_admin import KeycloakSettings, OAuth2Admin
import jose.jwt


kc_settings = KeycloakSettings()
oauth2_admin = OAuth2Admin(kc_settings)


def test_get_claims(mocker):
    token = "Test Token"
    mock_key_value = "secret"

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.content = "CONTENT"
    mock_resp.json = Mock(return_value=mock_key_value)

    mock_request = mocker.patch("requests.get", return_value=mock_resp)

    claims = {
        "token": token,
        "iss": kc_settings.kc_realm_url.unicode_string(),
        "audience": kc_settings.auth_client,
        "options": kc_settings._jwt_opts,
    }

    encoded = jose.jwt.encode(claims=claims, key=mock_key_value, algorithm="HS256")

    expected_result = jose.jwt.decode(
        token=encoded,
        key=mock_key_value,
        issuer=kc_settings.kc_realm_url.unicode_string(),
        audience=kc_settings.auth_client,
        options=kc_settings._jwt_opts,
    )

    actual_result = oauth2_admin.get_claims(encoded)

    mock_request.assert_called_with(kc_settings.certs_url)
    assert actual_result == expected_result


def test_update_user(mocker):
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


def test_associate_to_group(mocker):
    user_id = "test-id"
    group_id = "group-id"

    mock_group_user_add = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_group_user_add.return_value = None

    result = oauth2_admin.associate_to_group(user_id=user_id, group_id=group_id)
    assert result is None


def test_associate_to_lei(mocker):
    user_id = "test-id"
    lei = "TESTLEI"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = {"id": lei}

    mock_associate_to_group = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_associate_to_group.return_value = None

    result = oauth2_admin.associate_to_lei(user_id=user_id, lei=lei)
    assert result is None


def test_associate_to_lei_not_seeded(mocker):
    user_id = "test-id"
    lei = "TESTLEI"

    mock_get_group = mocker.patch("keycloak.KeycloakAdmin.get_group_by_path")
    mock_get_group.return_value = None

    mock_associate_to_group = mocker.patch("keycloak.KeycloakAdmin.group_user_add")
    mock_associate_to_group.return_value = None

    mock_create_group = mocker.patch("keycloak.KeycloakAdmin.create_group")
    mock_create_group.return_value = "test"

    oauth2_admin.associate_to_lei(user_id=user_id, lei=lei)
    mock_create_group.assert_called_with({"name": lei})


def test_associate_to_leis(mocker):
    user_id = ("test-id",)
    leis = Set["TESTLEI1", "TESTLEI2", "TESTLEI3"]  # noqa: F821

    associate_to_lei_mock = mocker.patch(
        "regtech_api_commons.oauth2.oauth2_admin.OAuth2Admin.associate_to_lei", return_value=None
    )

    oauth2_admin.associate_to_leis(user_id, leis)

    for lei in leis:
        associate_to_lei_mock.assert_called_with(user_id, lei)
