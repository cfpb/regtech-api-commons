from regtech_api_commons.models.auth import RegTechUser, AuthenticatedUser


def test_from_claims():
    test_claims = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
        "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
    }
    user = RegTechUser.from_claim(test_claims)

    assert user.name == test_claims.get("name")
    assert user.username == test_claims.get("preferred_username")
    assert user.email == test_claims.get("email")
    assert user.id == test_claims.get("sub")
    assert user.institutions == ["TEST1LEI", "TEST2CHILDLEI"]


def test_from_kc():
    kc_user = {
        "email": "test@local.host",
        "firstName": "test",
        "id": "testuser123",
        "lastName": "user",
        "username": "user1",
    }
    groups = [
        {"id": "test-id-1", "name": "TEST1LEI", "path": "/TEST1LEI"},
        {"id": "test-id-2", "name": "TEST2CHILDLEI", "path": "/TEST2LEI/TEST2CHILDLEI"},
    ]
    user = RegTechUser.from_kc(kc_user, groups)

    assert user.name == " ".join([kc_user.get("firstName"), kc_user.get("lastName")])
    assert user.username == kc_user.get("username")
    assert user.email == kc_user.get("email")
    assert user.id == kc_user.get("id")
    assert user.institutions == ["TEST1LEI", "TEST2CHILDLEI"]


def test_parse_institutions():
    test_claims_with_institutions = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
        "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
    }
    assert RegTechUser.from_claim(test_claims_with_institutions).institutions == ["TEST1LEI", "TEST2CHILDLEI"]

    test_claims_without_institutions = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
    }

    assert RegTechUser.from_claim(test_claims_without_institutions).institutions == []


def test_is_authenticated():
    test_claims = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
        "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
    }

    assert AuthenticatedUser.from_claim(test_claims).is_authenticated is True
