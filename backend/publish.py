import hashlib
import json
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import tomllib
from pydantic import BaseModel, Field
from rich import print as rprint
from syft_core import Client
from typer import Abort

from constant import RouterServiceType, PricingChargeType
from serializer import ProjectMetadata, ServiceOverview


class PublishService:
    """Service for publishing projects."""

    def __init__(self, client_config_path: Union[str, Path]):
        """Initialize the publish service with client configuration."""
        self.client_config_path = Path(client_config_path)
        self.client = Client.load(self.client_config_path)

    def _get_project_version(self, project_path: Path) -> str:
        """Extract project version from pyproject.toml."""
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return "0.1.0"

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("project", {}).get("version", "0.1.0")
        except Exception as e:
            rprint(
                f"[yellow]Warning: Could not read version from pyproject.toml: {e}[/yellow]"
            )
            return "0.1.0"

    def _calculate_code_hash(self, project_path: Path) -> str:
        """Calculate SHA256 hash of all Python files in the project."""
        hash_sha256 = hashlib.sha256()

        for py_file in project_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, "rb") as f:
                        hash_sha256.update(f.read())
                except Exception as e:
                    rprint(f"[yellow]Warning: Could not read {py_file}: {e}[/yellow]")

        return hash_sha256.hexdigest()

    def _get_schema_path(self, apps_data_dir: Path) -> Optional[str]:
        """Get the path to the RPC schema file."""
        schema_path = apps_data_dir / "rpc" / "rpc.schema.json"
        return str(schema_path) if schema_path.exists() else None

    def publish(
        self,
        project_name: str,
        project_folder_path: Union[str, Path],
        description: str,
        summary: str,
        tags: list[str],
        services: list[ServiceOverview],
    ) -> tuple[ProjectMetadata, Path]:
        """
        Publish a project.

        Args:
            project_name: Name of the project
            project_folder_path: Path to the project folder
            description: Project description
            summary: Project summary
            tags: Project tags
            pricing: Pricing information

        Returns:
            Path to the published project directory
        """
        project_path = Path(project_folder_path)

        if not project_path.exists():
            raise Abort(f"Project folder does not exist: {project_path}")

        if not project_path.is_dir():
            raise Abort(f"Project path is not a directory: {project_path}")

        # Get client directories
        apps_data_dir = self.client.app_data(project_name)

        # Derive metadata from project
        code_hash = self._calculate_code_hash(project_path)
        version = self._get_project_version(project_path)
        schema_path = self._get_schema_path(apps_data_dir)

        # Create metadata
        metadata = ProjectMetadata(
            project_name=project_name,
            description=description,
            summary=summary,
            tags=tags,
            services=services,
            code_hash=code_hash,
            version=version,
            documented_endpoints={},  # Skip for now as per requirements
            publish_date=datetime.now(),
            author=str(self.client.email),
            schema_path=schema_path,
        )

        # Write metadata.json
        metadata_path = (
            self.client.my_datasite
            / "public"
            / "routers"
            / project_name
            / "metadata.json"
        )

        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(metadata.model_dump_json())

        return metadata, metadata_path


def publish_project(
    project_name: str,
    project_folder_path: Union[str, Path],
    description: str,
    summary: str,
    tags: list[str],
    services: list[ServiceOverview],
    client_config_path: Union[str, Path],
) -> tuple[ProjectMetadata, Path]:
    """
    Convenience function to publish a project.

    Args:
        project_name: Name of the project
        project_folder_path: Path to the project folder
        description: Project description
        summary: Project summary
        tags: Project tags
        services: List of services with pricing information
        client_config_path: Path to client configuration file

    Returns:
        Path to the published project directory
    """

    service = PublishService(client_config_path)
    return service.publish(
        project_name=project_name,
        project_folder_path=project_folder_path,
        description=description,
        summary=summary,
        tags=tags,
        services=services,
    )
