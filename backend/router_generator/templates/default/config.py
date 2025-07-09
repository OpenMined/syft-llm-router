"""Default configuration for router."""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class RouterConfig:
    """Configuration for the router."""

    project_name: str
    enable_chat: bool = True
    enable_search: bool = True
    rag_url: str


def load_config() -> RouterConfig:
    """Load configuration from environment variables."""
    # Required fields
    project_name = os.getenv("PROJECT_NAME")
    if not project_name:
        raise ValueError("PROJECT_NAME is required in environment variables")

    # Optional fields with defaults
    enable_chat = os.getenv("ENABLE_CHAT", "true").lower() == "true"
    enable_search = os.getenv("ENABLE_RETRIEVE", "true").lower() == "true"
    rag_url = os.getenv("RAG_URL", "http://localhost:9000")

    return RouterConfig(
        project_name=project_name,
        enable_chat=enable_chat,
        enable_search=enable_search,
        rag_url=rag_url,
    )
