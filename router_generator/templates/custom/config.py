"""Custom configuration template for router.

Add your custom configuration options here.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class RouterConfig:
    """Configuration for the custom router."""

    project_name: str
    enable_chat: bool = True
    enable_retrieve: bool = True

    # TODO: Add your custom configuration fields here
    # Example:
    # custom_api_key: str = ""
    # custom_base_url: str = ""
    # custom_database_url: str = ""


def load_config() -> RouterConfig:
    """Load configuration from environment variables."""
    # Required fields
    project_name = os.getenv("PROJECT_NAME")
    if not project_name:
        raise ValueError("PROJECT_NAME is required in environment variables")

    # Optional fields with defaults
    enable_chat = os.getenv("ENABLE_CHAT", "true").lower() == "true"
    enable_retrieve = os.getenv("ENABLE_RETRIEVE", "true").lower() == "true"

    # TODO: Load your custom configuration from environment variables
    # Example:
    # custom_api_key = os.getenv("CUSTOM_API_KEY", "")
    # custom_base_url = os.getenv("CUSTOM_BASE_URL", "")
    # custom_database_url = os.getenv("CUSTOM_DATABASE_URL", "")

    return RouterConfig(
        project_name=project_name,
        enable_chat=enable_chat,
        enable_retrieve=enable_retrieve,
        # TODO: Add your custom fields here
        # custom_api_key=custom_api_key,
        # custom_base_url=custom_base_url,
        # custom_database_url=custom_database_url,
    )
