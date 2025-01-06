import logging
from typing import Dict, Any, Set

import json
import jwt
import requests

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection, exceptions as kce

from regtech_api_commons.models.auth import RegTechUser
from regtech_api_commons.api.exceptions import RegTechHttpException

from regtech_api_commons.oauth2.config import KeycloakSettings
from regtech_regex.regex_config import RegexConfigs

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
            # Get the key id from the token header, and use that to find
            # the correct public key from Keycloak.  Then use the public key
            # to decode the token and get the claims
            kid = jwt.get_unverified_header(token).get("kid")
            keys = self._get_keys()
            key = next((key for key in keys["keys"] if key["kid"] == kid), None)
            if not key:
                pass
            return jwt.decode(
                jwt=token,
                key=jwt.PyJWK.from_json(json.dumps(key)),
                issuer=self._kc_settings.kc_realm_url.unicode_string(),
                audience=self._kc_settings.auth_client,
                options=self._kc_settings._jwt_opts,
            )
        except jwt.exceptions.ExpiredSignatureError:
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
            log.exception("Failed to update user: %s", user_id)
            raise RegTechHttpException(status_code=e.response_code, detail="Failed to update user")

    def upsert_group(self, lei: str, name: str) -> str:
        try:
            group_payload = {"name": lei}
            group = self.get_group(lei)
            if group is None:
                return self._admin.create_group(group_payload)
            else:
                self._admin.update_group(group["id"], group_payload)
                return group["id"]
        except kce.KeycloakError as e:
            log.exception("Failed to upsert group, lei: %s, name: %s", lei, name)
            raise RegTechHttpException(status_code=e.response_code, detail="Failed to upsert group")

    def get_group(self, lei: str) -> Dict[str, Any] | None:
        try:
            group = self._admin.get_group_by_path(f"/{lei}")
            if group and "id" in group:
                return group
            else:
                log.error(f"Unexpected results from get_group_by_path: {group}")
                return None
        except kce.KeycloakError:
            return None

    def associate_to_group(self, user_id: str, group_id: str) -> None:
        try:
            self._admin.group_user_add(user_id, group_id)
        except kce.KeycloakError as e:
            log.exception("Failed to associate user %s to group %s", user_id, group_id)
            raise RegTechHttpException(status_code=e.response_code, detail="Failed to associate user to group")

    def associate_to_lei(self, user_id: str, lei: str) -> None:
        regex_configs = RegexConfigs.instance()
        if regex_configs.lei.regex.match(lei):
            group = self.get_group(lei)
            group_id = group["id"] if group else self._admin.create_group({"name": lei})
            if group_id:
                self.associate_to_group(user_id, group_id)
        else:
            raise ValueError(f"Invalid LEI {lei}. {regex_configs.lei.error_text}")

    def associate_to_leis(self, user_id: str, leis: Set[str]):
        for lei in leis:
            self.associate_to_lei(user_id, lei)

    def delete_group(self, lei: str) -> Dict[str, Any] | None:
        try:
            group = self.get_group(lei)
            return self._admin.delete_group(group["id"])
        except kce.KeycloakError as e:
            log.exception("Failed to delete group, lei: %s", lei)
            raise RegTechHttpException(status_code=e.response_code, detail="Failed to delete group")
