import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import tomllib
from rich import print as rprint
from syft_core import Client
from syft_core.permissions import PERM_FILE, SyftPermission
from typer import Abort

from .schemas import ProjectMetadata, ServiceOverview


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

    def _set_rpc_endpoints_visibility(self, apps_data_dir: Path, make_private: bool):
        """Set the visibility of the RPC endpoints.

        If make_private is True, the RPC endpoints will be private, only visible to the owner.
        If make_private is False, the RPC endpoints will be public, visible to all users.
        """
        rpc_path = apps_data_dir / PERM_FILE
        if rpc_path.exists():
            syft_perms = SyftPermission.from_file(rpc_path, apps_data_dir)
            syft_perms.terminal = make_private
            syft_perms.save(apps_data_dir)

    def _get_endpoint_details(
        self, project_name: str, project_path: Path
    ) -> dict[str, Any]:
        """Get the endpoint details for the project."""
        with open(project_path / f"{project_name}.openapi.json", "r") as f:
            data = json.load(f)
        return data

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
        endpoint_details = self._get_endpoint_details(project_name, project_path)

        # Create metadata
        metadata = ProjectMetadata(
            project_name=project_name,
            description=description,
            summary=summary,
            tags=tags,
            services=services,
            code_hash=code_hash,
            version=version,
            documented_endpoints=endpoint_details,
            publish_date=datetime.now(),
            author=str(self.client.email),
            schema_path=schema_path,
        )

        # Make RPC endpoints public i.e. visible to all users
        self._set_rpc_endpoints_visibility(apps_data_dir, make_private=False)

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

    def unpublish(self, project_name: str) -> None:
        """Unpublish a project.

        This function will unpublish a project by deleting the metadata.json file.
        """
        metadata_path = (
            self.client.my_datasite
            / "public"
            / "routers"
            / project_name
            / "metadata.json"
        )

        metadata_path.unlink(missing_ok=True)

        # Delete the project folder
        project_path = self.client.my_datasite / "public" / "routers" / project_name
        shutil.rmtree(project_path, ignore_errors=True)

        # Make RPC endpoints private i.e. only visible to the owner
        self._set_rpc_endpoints_visibility(
            self.client.app_data(project_name), make_private=True
        )


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


def unpublish_project(
    project_name: str,
    client_config_path: Union[str, Path],
) -> None:
    """Unpublish a project.

    This function will unpublish a project by deleting the metadata.json file
    and the project folder.

    Args:
        project_name: Name of the project
        client_config_path: Path to client configuration file
    """
    service = PublishService(client_config_path)
    service.unpublish(project_name)
