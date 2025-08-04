from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env if present
load_dotenv(override=True)

DEFAULT_ACCOUNTING_SERVICE_URL = "http://syftaccounting.centralus.cloudapp.azure.com"


class AppSettings(BaseSettings):
    app_name: str = Field("SyftRouter", env="APP_NAME")
    syftbox_config_path: Path = Field(
        "~/.syftbox/config.json", env="SYFTBOX_CONFIG_PATH"
    )
    accounting_service_url: str = Field(
        DEFAULT_ACCOUNTING_SERVICE_URL, env="ACCOUNTING_SERVICE_URL"
    )

    @field_validator("syftbox_config_path", mode="before")
    def validate_syftbox_config_path(cls, v):
        # Expand tilde to home directory
        expanded_path = Path(v).expanduser()
        path = expanded_path.resolve()
        if not path.exists():
            raise ValueError(f"Syftbox config path {path} does not exist")
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance for global access
settings = AppSettings()
