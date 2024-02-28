from typing import List, Dict, Any
from pydantic import BaseModel
from starlette.authentication import BaseUser


class RegTechUser(BaseModel):
    name: str
    username: str
    email: str
    id: str
    institutions: List[str]

    @classmethod
    def from_claim(cls, claims: Dict[str, Any]) -> "RegTechUser":
        return cls(
            name=claims.get("name", ""),
            username=claims.get("preferred_username", ""),
            email=claims.get("email", ""),
            id=claims.get("sub", ""),
            institutions=cls.parse_institutions(claims.get("institutions")),
        )

    @classmethod
    def from_kc(cls, user: Dict[str, Any], groups: List[Dict[str, Any]]) -> "RegTechUser":
        return cls(
            name=" ".join([user.get("firstName", ""), user.get("lastName", "")]),
            username=user.get("username", ""),
            email=user.get("email", ""),
            id=user.get("id", ""),
            institutions=cls.parse_institutions([group.get("path") for group in groups]),
        )

    @classmethod
    def parse_institutions(cls, institutions: List[str] | None) -> List[str]:
        """
        Parse out the list of institutions returned by Keycloak

        Args:
            institutions(List[str]): list of full institution paths provided by keycloak,
            it is possible to have nested paths, though we may not use the feature.
            e.g. ["/ROOT_INSTITUTION/CHILD_INSTITUTION/GRAND_CHILD_INSTITUTION"]

        Returns:
            List[str]: List of cleaned up institutions.
            e.g. ["GRAND_CHILD_INSTITUTION"]
        """
        if institutions:
            return [institution.split("/")[-1] for institution in institutions]
        else:
            return []


class AuthenticatedUser(BaseUser, RegTechUser):
    @property
    def is_authenticated(self) -> bool:
        return True
