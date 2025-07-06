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
    enable_retrieve: bool = True
    ollama_base_url: str = "http://localhost:11434"
    chroma_db_path: str = "./chroma_db"


def load_config() -> RouterConfig:
    """Load configuration from environment variables."""
    # Required fields
    project_name = os.getenv("PROJECT_NAME")
    if not project_name:
        raise ValueError("PROJECT_NAME is required in environment variables")

    # Optional fields with defaults
    enable_chat = os.getenv("ENABLE_CHAT", "true").lower() == "true"
    enable_retrieve = os.getenv("ENABLE_RETRIEVE", "true").lower() == "true"
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")

    return RouterConfig(
        project_name=project_name,
        enable_chat=enable_chat,
        enable_retrieve=enable_retrieve,
        ollama_base_url=ollama_base_url,
        chroma_db_path=chroma_db_path,
    )
