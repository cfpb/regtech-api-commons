import pytest
from regtech_api_commons.oauth2.config import KeycloakSettings


def test_jwt_opts_valid_values():
    mock_config = {
        "jwt_opts_test1": "true",
        "jwt_opts_test2": "true",
        "jwt_opts_test3": "12",
    }
    kc_settings = KeycloakSettings(**mock_config)
    assert kc_settings._jwt_opts == {"test1": True, "test2": True, "test3": 12}


def test_jwt_opts_invalid_values():
    mock_config = {
        "jwt_opts_test1": "not a bool or int",
        "jwt_opts_test2": "true",
        "jwt_opts_test3": "12",
    }
    with pytest.raises(Exception) as e:
        KeycloakSettings(**mock_config)
    assert "validation error" in str(e.value)


def test_all_envs_optional():
    KeycloakSettings()
