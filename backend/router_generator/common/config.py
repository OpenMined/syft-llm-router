"""Shared configuration system for router templates.

This module provides the unified configuration system that loads from state.json first,
then falls back to environment variables. Uses Pydantic for type safety and validation.
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


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


class StateFile(BaseModel):
    """Complete state file structure."""

    project: ProjectInfo
    configuration: RouterConfiguration
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


class RouterConfig:
    """Simplified router configuration that wraps StateFile for easy access."""

    def __init__(self, state_file: StateFile):
        """Initialize with a StateFile instance."""
        self._state = state_file

    @property
    def project_name(self) -> str:
        """Get project name."""
        return self._state.project.name

    @property
    def enable_chat(self) -> bool:
        """Check if chat is enabled."""
        return self._state.configuration.enable_chat

    @property
    def enable_search(self) -> bool:
        """Check if search is enabled."""
        return self._state.configuration.enable_search

    @property
    def service_urls(self) -> Dict[str, str]:
        """Get URLs of running services."""
        urls = {}
        for service_name, service_state in self._state.services.items():
            if service_state.status == RunStatus.RUNNING and service_state.url:
                urls[service_name] = service_state.url
        return urls

    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get URL for a specific service."""
        service_state = self._state.services.get(service_name)
        if service_state and service_state.status == RunStatus.RUNNING:
            return service_state.url
        return None

    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        if service_name == "chat":
            return self.enable_chat
        elif service_name == "search":
            return self.enable_search
        return False

    @property
    def state(self) -> StateFile:
        """Get the underlying StateFile for advanced operations."""
        return self._state

    @classmethod
    def from_state_file(cls, state_file: str = "state.json") -> "RouterConfig":
        """Load configuration from state.json file."""
        state_path = Path(state_file)
        load_dotenv(override=True)

        if not state_path.exists():
            # Fallback to environment variables
            return cls.from_env()

        try:
            state = StateFile.load(state_path)
            return cls(state)
        except Exception as e:
            print(f"Warning: Failed to load state file {state_file}: {e}")
            # Fallback to environment variables
            return cls.from_env()

    @classmethod
    def from_env(cls) -> "RouterConfig":
        """Load configuration from environment variables."""
        # Load .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

        # Required fields
        project_name = os.getenv("PROJECT_NAME")
        if not project_name:
            raise ValueError("PROJECT_NAME is required in environment variables")

        # Optional fields with defaults
        enable_chat = os.getenv("ENABLE_CHAT", "true").lower() == "true"
        enable_search = os.getenv("ENABLE_SEARCH", "true").lower() == "true"

        # Create a minimal StateFile from environment
        state = StateFile(
            project=ProjectInfo(name=project_name, version="1.0.0"),
            configuration=RouterConfiguration(
                enable_chat=enable_chat, enable_search=enable_search
            ),
            services={},
            router=RouterState(status=RunStatus.STOPPED),
        )

        # Add service URLs from environment if available
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_url:
            state.services["chat"] = ServiceState(
                status=RunStatus.RUNNING, url=ollama_url
            )

        rag_url = os.getenv("RAG_SERVICE_URL")
        if rag_url:
            state.services["search"] = ServiceState(
                status=RunStatus.RUNNING, url=rag_url
            )

        return cls(state)


def load_config() -> RouterConfig:
    """Load configuration using state-first approach.

    Returns:
        RouterConfig: The loaded configuration

    Raises:
        ValueError: If required configuration is missing
    """
    return RouterConfig.from_state_file()
