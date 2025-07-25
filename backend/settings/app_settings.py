from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import secrets

# Load environment variables from .env if present
load_dotenv(override=True)


class AppSettings(BaseSettings):
    app_name: str = Field("SyftRouter", env="APP_NAME")
    accounting_url: str = Field(..., env="ACCOUNTING_URL")
    accounting_email: str = Field(..., env="ACCOUNTING_EMAIL")
    accounting_password: str = Field(..., env="ACCOUNTING_PASSWORD")
    syftbox_config_path: str = Field(
        "~/.syftbox/config.json", env="SYFTBOX_CONFIG_PATH"
    )

    @model_validator(mode="after")
    def set_accounting_password(self):
        if not self.accounting_password:
            self.accounting_password = secrets.token_hex(16)
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance for global access
settings = AppSettings()
