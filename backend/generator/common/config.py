"""Shared configuration system for router templates.

This module provides the unified configuration system that loads from state.json first,
then falls back to environment variables. Uses Pydantic for type safety and validation.
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, EmailStr, Field
from syft_accounting_sdk import UserClient
from dotenv import load_dotenv
from syft_core.config import SyftClientConfig


class RunStatus(str, Enum):
    """Represents the state of a service."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class ServiceState(BaseModel):
    """Represents the runtime state of a service."""

    status: RunStatus = Field(
        ..., description="Service status: running, stopped, failed"
    )
    url: Optional[str] = Field(None, description="Service URL")
    port: Optional[int] = Field(None, description="Service port")
    pid: Optional[int] = Field(None, description="Process ID")
    started_at: Optional[str] = Field(None, description="Service start timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class RouterState(BaseModel):
    """Represents the runtime state of the router."""

    status: RunStatus = Field(
        ..., description="Router status: running, stopped, failed"
    )
    started_at: Optional[str] = Field(None, description="Router start timestamp")
    depends_on: list[str] = Field(
        default_factory=list, description="Service dependencies"
    )
    url: Optional[str] = Field(None, description="Router URL")


class ProjectInfo(BaseModel):
    """Project metadata."""

    name: str = Field(..., description="Project name")
    version: str = Field(default="1.0.0", description="Project version")


class RouterConfiguration(BaseModel):
    """Router configuration settings."""

    enable_chat: bool = Field(default=True, description="Enable chat service")
    enable_search: bool = Field(default=True, description="Enable search service")


class AccountingConfig(BaseModel):
    """Accounting configuration."""

    url: str
    email: EmailStr
    password: str

    @property
    def client(self) -> UserClient:
        """Get user client."""
        return UserClient(
            url=self.url,
            email=self.email,
            password=self.password,
        )


class StateFile(BaseModel):
    """Runtime state file structure (services and router only)."""

    services: Dict[str, ServiceState] = Field(default_factory=dict)
    router: RouterState = Field(default_factory=lambda: RouterState(status="stopped"))

    def update_service_state(self, service_name: str, **kwargs):
        """Update the state of a specific service."""
        if service_name not in self.services:
            self.services[service_name] = ServiceState(status=RunStatus.STOPPED)

        # Update the service state with new values
        current_state = self.services[service_name]
        for key, value in kwargs.items():
            if hasattr(current_state, key):
                setattr(current_state, key, value)
        self.save()

    def update_router_state(self, **kwargs):
        """Update the state of the router."""
        for key, value in kwargs.items():
            if hasattr(self.router, key):
                setattr(self.router, key, value)
        self.save()

    def save(self, state_file: str = "state.json") -> None:
        """Save the state to a file."""
        with open(state_file, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    @classmethod
    def load(cls, state_file: str = "state.json") -> "StateFile":
        """Load the state from a file."""
        with open(state_file, "r") as f:
            return cls.model_validate(json.load(f))


class RouterConfig(BaseModel):
    """Aggregates static config and runtime state for the router."""

    project: ProjectInfo
    configuration: RouterConfiguration
    state: StateFile
    accounting: AccountingConfig
    syft_config: SyftClientConfig

    @property
    def project_name(self) -> str:
        return self.project.name

    @property
    def enable_chat(self) -> bool:
        return self.configuration.enable_chat

    @property
    def enable_search(self) -> bool:
        return self.configuration.enable_search

    @property
    def service_urls(self) -> Dict[str, str]:
        urls = {}
        for service_name, service_state in self.state.services.items():
            if service_state.status == RunStatus.RUNNING and service_state.url:
                urls[service_name] = service_state.url
        return urls

    def get_service_url(self, service_name: str) -> Optional[str]:
        service_state = self.state.services.get(service_name)
        if service_state and service_state.status == RunStatus.RUNNING:
            return service_state.url
        return None

    def is_service_enabled(self, service_name: str) -> bool:
        if service_name == "chat":
            return self.enable_chat
        elif service_name == "search":
            return self.enable_search
        return False

    def accounting_client(self) -> UserClient:
        return self.accounting.client

    @classmethod
    def load(
        cls,
        syft_config_path: Path,
        state_file: str = "state.json",
        env_file: str = ".env",
    ) -> "RouterConfig":
        """
        Loads runtime state from state_file, and static config from environment variables (or config file if provided).
        """
        state_path = Path(state_file)
        if state_path.exists():
            try:
                state = StateFile.load(state_path)
            except Exception as e:
                print(f"Warning: Failed to load state file: {e}")
                state = StateFile(
                    services={}, router=RouterState(status=RunStatus.STOPPED)
                )
        else:
            state = StateFile(services={}, router=RouterState(status=RunStatus.STOPPED))

        # Load environment variables from .env file
        load_dotenv(env_file, override=True)

        # Load required environment variables from os.environ
        required_env_vars = [
            "PROJECT_NAME",
            "ENABLE_CHAT",
            "ENABLE_SEARCH",
            "ACCOUNTING_URL",
            "ACCOUNTING_EMAIL",
            "ACCOUNTING_PASSWORD",
        ]
        for var in required_env_vars:
            if var not in os.environ:
                raise ValueError(f"{var} is required in environment variables")

        project_name = os.environ["PROJECT_NAME"]
        enable_chat = os.environ["ENABLE_CHAT"].lower() == "true"
        enable_search = os.environ["ENABLE_SEARCH"].lower() == "true"
        project = ProjectInfo(name=project_name, version="1.0.0")
        configuration = RouterConfiguration(
            enable_chat=enable_chat, enable_search=enable_search
        )
        accounting = AccountingConfig(
            url=os.environ["ACCOUNTING_URL"],
            email=os.environ["ACCOUNTING_EMAIL"],
            password=os.environ["ACCOUNTING_PASSWORD"],
        )

        syft_config = SyftClientConfig.load(syft_config_path)
        return cls(project, configuration, state, accounting, syft_config)


def load_config(
    syft_config_path: Path,
    state_file: str = "state.json",
    env_file: str = ".env",
) -> RouterConfig:
    return RouterConfig.load(syft_config_path, state_file, env_file)
