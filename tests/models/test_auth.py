from regtech_api_commons.models import AuthenticatedUser

test_claims = {
    "name": "test",
    "preferred_username": "test_user",
    "email": "test@local.host",
    "sub": "testuser123",
    "institutions": ["/TEST1LEI", "/TEST2LEI/TEST2CHILDLEI"],
}


def test_correct_from_claims():
    test_authenticated_user = AuthenticatedUser(
        claims=test_claims,
        name=test_claims.get("name"),
        username=test_claims.get("preferred_username"),
        email=test_claims.get("email"),
        id=test_claims.get("sub"),
        institutions=AuthenticatedUser.parse_institutions(test_claims.get("institutions")),
    )

    assert AuthenticatedUser.from_claim(test_claims) == test_authenticated_user


def test_incorrect_from_claims():
    test_authenticated_user = AuthenticatedUser(
        claims=test_claims,
        name="test_user_incorrect",
        username="test_incorrect_username",
        email="test_incorrect@local.host",
        id="test_incorrect_id",
        institutions=["/incorrect_institution_1", "/incorrect_institution_2"],
    )

    assert AuthenticatedUser.from_claim(test_claims) != test_authenticated_user


def test_parse_institutions_correct():
    assert AuthenticatedUser.parse_institutions(test_claims.get("institutions")) == ["TEST1LEI", "TEST2CHILDLEI"]
    assert AuthenticatedUser.parse_institutions(institutions=None) == []


def test_parse_institutions_incorrect():
    assert AuthenticatedUser.parse_institutions(test_claims.get("institutions")) != [
        "/TESTLEI",
        "/TEST2LEI/TEST2CHILDLEI",
    ]
    assert AuthenticatedUser.parse_institutions(institutions=None) != ["TESTLEI"]


def test_is_authenticated():
    test_authenticated_user = AuthenticatedUser(
        claims=test_claims,
        name=test_claims.get("name"),
        username=test_claims.get("preferred_username"),
        email=test_claims.get("email"),
        id=test_claims.get("sub"),
        institutions=AuthenticatedUser.parse_institutions(test_claims.get("institutions")),
    )

    assert test_authenticated_user.is_authenticated is True
