from typing import Annotated
from pydantic import Field, model_validator, ConfigDict

from .baseconfig import BaseAddonConfig, RequiredSecretsBase

class CustomRequiredSecrets(RequiredSecretsBase):
    google_drive_access_token: str = Field(..., description="Google Drive API access token environment variable name (key name expected in `secrets`).")

class CustomAddonConfig(BaseAddonConfig):
    model_config = ConfigDict(extra="allow")

    page_size: int = Field(100, description="Taille de page par défaut")
    max_page_size: int = Field(1000, description="Taille de page maximale autorisée")

    @classmethod
    def get_required_secrets(cls) -> CustomRequiredSecrets:
        return CustomRequiredSecrets(google_drive_access_token="google_drive_access_token")

    @model_validator(mode="after")
    def validate_google_drive_secrets(self):
        required = self.get_required_secrets()
        required_secret_keys = [required.google_drive_access_token]

        missing = [k for k in required_secret_keys if not self.secrets.get(k)]
        if missing:
            raise ValueError("Missing Google Drive secrets: "f"{missing}. Put your OAuth access token under these keys in `secrets`.")
        return self
