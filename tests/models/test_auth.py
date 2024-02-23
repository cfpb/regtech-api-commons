from regtech_api_commons.models import AuthenticatedUser


def test_from_claims():
    test_claims = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
        "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
    }
    test_authenticated_user = AuthenticatedUser(
        claims=test_claims,
        name=test_claims.get("name"),
        username=test_claims.get("preferred_username"),
        email=test_claims.get("email"),
        id=test_claims.get("sub"),
        institutions=AuthenticatedUser.parse_institutions(test_claims.get("institutions")),
    )

    assert AuthenticatedUser.from_claim(test_claims) == test_authenticated_user


def test_parse_institutions():
    test_claims_with_institutions = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
        "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
    }
    assert AuthenticatedUser.from_claim(test_claims_with_institutions).institutions == ["TEST1LEI", "TEST2CHILDLEI"]

    test_claims_without_institutions = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
    }

    assert AuthenticatedUser.from_claim(test_claims_without_institutions).institutions == []


def test_is_authenticated():
    test_claims = {
        "name": "test",
        "preferred_username": "test_user",
        "email": "test@local.host",
        "sub": "testuser123",
        "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
    }
    test_authenticated_user = AuthenticatedUser(
        claims=test_claims,
        name=test_claims.get("name"),
        username=test_claims.get("preferred_username"),
        email=test_claims.get("email"),
        id=test_claims.get("sub"),
        institutions=AuthenticatedUser.parse_institutions(test_claims.get("institutions")),
    )

    assert test_authenticated_user.is_authenticated is True
