import json
import os
from pathlib import Path
from typing import Optional
from syft_core import Client as SyftBoxClient
from accountingSDK import UserClient

from pydantic import BaseModel


class AccountingConfig(BaseModel):
    email: str
    password: str
    url: str

    @staticmethod
    def load(path: Path):
        with open(path) as f:
            config = json.load(f)
        return AccountingConfig(**config)

    def save(self, path: Path):
        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f)


def get_or_init_user_client(
    syftbox_config_path: Optional[Path] = None,
    accounting_config_path: Optional[Path] = None,
):
    if syftbox_config_path:
        syftbox_client = SyftBoxClient.load(syftbox_config_path)
    else:
        syftbox_client = SyftBoxClient.load()

    if not accounting_config_path:
        accounting_config_path = Path.home() / ".syftbox" / "accounting-config.json"
    else:
        accounting_config_path = Path(accounting_config_path).expanduser()

    if accounting_config_path.is_file():
        accounting_config = AccountingConfig.load(accounting_config_path)
        return UserClient(
            url=accounting_config.url,
            email=accounting_config.email,
            password=accounting_config.password,
        )

    email = syftbox_client.email
    url = os.environ.get("ACCOUNTING_SERVICE_URL")

    _, password = UserClient.create_user(url=url, email=email)

    accounting_config = AccountingConfig(url=url, email=email, password=password)
    accounting_config.save(accounting_config_path)

    return UserClient(url=url, email=email, password=password) 