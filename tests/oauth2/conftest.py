import os
from regtech_api_commons.oauth2.config import KeycloakSettings

env_files_to_load = [".test-env"]
if os.getenv("ENV", "LOCAL") == "LOCAL":
    env_files_to_load.append(".test-env.local")

kc_settings = KeycloakSettings(_env_file=env_files_to_load)
