from http import HTTPStatus
import logging
from typing import Dict, Any, Set

import jose.jwt
import requests
from fastapi import HTTPException

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection, exceptions as kce

from ..models.auth import RegTechUser

from .config import KeycloakSettings

log = logging.getLogger(__name__)


class OAuth2Admin:
    def __init__(self, kc_settings: KeycloakSettings) -> None:
        self._kc_settings = kc_settings
        self._keys = None
        conn = KeycloakOpenIDConnection(
            server_url=self._kc_settings.kc_url.unicode_string(),
            realm_name=self._kc_settings.kc_realm,
            client_id=self._kc_settings.kc_admin_client_id,
            client_secret_key=self._kc_settings.kc_admin_client_secret.get_secret_value(),
        )
        self._admin = KeycloakAdmin(connection=conn)

    def get_claims(self, token: str) -> Dict[str, str] | None:
        try:
            return jose.jwt.decode(
                token=token,
                key=self._get_keys(),
                issuer=self._kc_settings.kc_realm_url.unicode_string(),
                audience=self._kc_settings.auth_client,
                options=self._kc_settings.jwt_opts,
            )
        except jose.ExpiredSignatureError:
            pass

    def _get_keys(self) -> Dict[str, Any]:
        if self._keys is None:
            response = requests.get(self._kc_settings.certs_url)
            self._keys = response.json()
        return self._keys

    def get_user(self, user_id: str) -> RegTechUser:
        user = self._admin.get_user(user_id)
        groups = self._admin.get_user_groups(user_id)
        return RegTechUser.from_kc(user, groups)

    def update_user(self, user_id: str, payload: Dict[str, Any]) -> None:
        try:
            self._admin.update_user(user_id, payload)
        except kce.KeycloakError as e:
            log.exception("Failed to update user: %s", user_id, extra=payload)
            raise HTTPException(status_code=e.response_code, detail="Failed to update user")

    def upsert_group(self, lei: str, name: str) -> str:
        try:
            group_payload = {"name": lei, "attributes": {"fi_name": [name]}}
            group = self.get_group(lei)
            if group is None:
                return self._admin.create_group(group_payload)
            else:
                self._admin.update_group(group["id"], group_payload)
                return group["id"]
        except kce.KeycloakError as e:
            log.exception("Failed to upsert group, lei: %s, name: %s", lei, name)
            raise HTTPException(status_code=e.response_code, detail="Failed to upsert group")

    def get_group(self, lei: str) -> Dict[str, Any] | None:
        try:
            return self._admin.get_group_by_path(f"/{lei}")
        except kce.KeycloakError:
            return None

    def associate_to_group(self, user_id: str, group_id: str) -> None:
        try:
            self._admin.group_user_add(user_id, group_id)
        except kce.KeycloakError as e:
            log.exception("Failed to associate user %s to group %s", user_id, group_id)
            raise HTTPException(status_code=e.response_code, detail="Failed to associate user to group")

    def associate_to_lei(self, user_id: str, lei: str) -> None:
        group = self.get_group(lei)
        if group is not None:
            self.associate_to_group(user_id, group["id"])
        else:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="No institution found for given LEI",
            )

    def associate_to_leis(self, user_id: str, leis: Set[str]):
        for lei in leis:
            self.associate_to_lei(user_id, lei)
