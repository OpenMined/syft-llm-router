import hashlib
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import tomllib
from pydantic import BaseModel, Field, field_validator
from rich import print as rprint
from syft_core import Client
from typer import Abort


class PricingMethod(str, Enum):
    """Pricing methods for the LLM Router."""

    PER_REQUEST = "per-request"
    PER_TOKENS = "per-tokens"
    FREE = "free"

    @classmethod
    def get_choices(cls) -> list[str]:
        """Return a list of choices for the pricing method."""
        return [method.value for method in cls]

    def __str__(self) -> str:
        """Return a human-readable description of the pricing method."""
        descriptions = {
            "per-request": "Pay per API request",
            "per-tokens": "Pay per token usage",
            "free": "Free to use",
        }
        return f"{self.value} - {descriptions[self.value]}"


class Pricing(BaseModel):
    """Handles pricing generation and validation for LLM Router implementations."""

    method: PricingMethod
    price: float


class PublishConfig(BaseModel):
    """Configuration for publishing a project."""

    folder: Path
    description: str
    tags: str
    readme: Path
    client_config: Optional[Path] = None
    pricing: Pricing

    @field_validator("folder", "readme", "client_config", mode="before")
    def convert_to_path(cls, v: Optional[Union[str, Path]]) -> Optional[Path]:
        """Convert string to Path if necessary."""
        if v is None:
            return None
        return Path(v)


class ProjectMetadata(BaseModel):
    """Handles metadata generation and validation for LLM Router implementations."""

    project_folder: Path
    required_files: list[str] = Field(
        default=["router.py", "server.py", "pyproject.toml", "run.sh"]
    )

    @field_validator("project_folder", mode="before")
    def convert_to_path(cls, v: Union[str, Path]) -> Path:
        """Convert string to Path if necessary."""
        return Path(v)

    def validate_project_structure(self) -> bool:
        """Validate that the project has all required files.

        Returns:
            bool: True if all required files exist, False otherwise.
        """
        missing_files = [
            file
            for file in self.required_files
            if not (self.project_folder / file).exists()
        ]

        if missing_files:
            rprint(f"[red]Missing required files: {', '.join(missing_files)}[/red]")
            return False
        return True

    def generate_code_hash(self) -> str:
        """Generate a SHA-256 hash of the code files.

        Returns:
            str: Hexadecimal representation of the hash.
        """
        hasher = hashlib.sha256()

        for file in ["router.py", "server.py"]:
            file_path = self.project_folder / file
            try:
                hasher.update(file_path.read_bytes())
            except Exception as e:
                rprint(f"[red]Error reading {file}: {str(e)}[/red]")
                raise

        return hasher.hexdigest()

    def read_project_metadata(self) -> dict[str, Any]:
        """Read and parse metadata from pyproject.toml.

        Returns:
            Dict: Parsed TOML content or empty dict if file doesn't exist.
        """
        toml_path = self.project_folder / "pyproject.toml"
        if not toml_path.exists():
            rprint("[yellow]pyproject.toml not found[/yellow]")
            return {}

        try:
            return tomllib.loads(toml_path.read_text())
        except Exception as e:
            rprint(f"[red]Error parsing pyproject.toml: {str(e)}[/red]")
            return {}

    def generate(
        self,
        project_name: str,
        description: str,
        tags: list[str],
        readme_content: str,
        documented_endpoints: dict[str, Any],
        pricing: Pricing,
    ) -> dict[str, Any]:
        """Generate metadata dictionary with all project information.

        Args:
            project_name: Name of the project
            description: Project description
            tags: List of tags for categorization
            readme_content: Content of the README file
            documented_endpoints: List of documented endpoints with their descriptions
            pricing_method: Pricing method
            price: Price of the router

        Returns:
            Dict: Complete metadata dictionary

        Raises:
            ValueError: If project structure is invalid
        """
        if not self.validate_project_structure():
            raise ValueError(
                "Invalid project structure. "
                "Please ensure all required files are present. "
                "Required files: " + ", ".join(self.required_files)
            )

        project_metadata = self.read_project_metadata()

        return {
            "project_name": project_name,
            "description": description,
            "tags": tags,
            "version": project_metadata.get("project", {}).get("version", "0.1.0"),
            "dependencies": project_metadata.get("project", {}).get("dependencies", []),
            "code_hash": self.generate_code_hash(),
            "readme": readme_content,
            "documented_endpoints": documented_endpoints or {},
            "publish_date": datetime.now().isoformat(),
            "pricing": f"{pricing.method.value} - {pricing.price}",
        }


class PublishHandler:
    """Handles the publishing process for LLM Router implementations."""

    def __init__(
        self,
        folder: Path,
        description: str,
        tags: str,
        readme: Path,
        pricing_method: PricingMethod,
        price: float,
        client_config: Optional[Path] = None,
    ) -> None:
        """Initialize the publish handler with required parameters.

        Args:
            folder: Path to the project directory
            description: Project description
            tags: Comma-separated list of tags
            readme: Path to README file
            client_config: Optional path to Syft client config file
        """
        self.config = PublishConfig(
            folder=folder,
            description=description,
            tags=tags,
            readme=readme,
            client_config=client_config,
            pricing=Pricing(method=pricing_method, price=price),
        )

    def validate_paths(self) -> bool:
        """Validate that all provided paths exist.

        Returns:
            bool: True if all paths are valid, False otherwise
        """
        if not self.config.folder.exists():
            rprint(
                "[red]Error: Project directory does not exist: "
                f"{self.config.folder}[/red]"
            )
            return False

        if not self.config.readme.exists():
            rprint(
                f"[red]Error: README file does not exist: {self.config.readme}[/red]"
            )
            return False

        if not self.config.readme.is_file():
            rprint(f"[red]Error: README file is not a file: {self.config.readme}[/red]")
            return False

        return True

    def get_readme_content(self) -> str:
        """Get the content of the README file if it exists.

        Returns:
            str: Content of the README file or empty string if not provided
        """
        return self.config.readme.read_text()

    def get_documented_endpoints(self, client: Client, name: str) -> dict[str, Any]:
        """Get the documented endpoints from the RPC schema.

        Args:
            client: Syft client instance
            name: Name of the project

        Returns:
            dict: Documented endpoints or empty dict if schema doesn't exist
        """
        if name.startswith("com.git.hub.openmined."):
            name = name.replace("com.git.hub.openmined.", "")
        app_name = f"llm/{name}"
        rpc_schema_path = client.app_data(app_name) / "rpc/rpc.schema.json"

        if not rpc_schema_path.exists():
            rprint(
                f"[yellow]RPC schema file does not exist at: {rpc_schema_path}[/yellow]"
            )
            return {}

        try:
            return json.loads(rpc_schema_path.read_text())
        except Exception as e:
            rprint(f"[red]Error reading RPC schema: {str(e)}[/red]")
            return {}

    def process_tags(self) -> list[str]:
        """Process the tags string into a list of tags.

        Returns:
            list[str]: List of processed tags
        """
        return [tag.strip() for tag in self.config.tags.split(",")]

    def release_metadata(self, metadata: dict[str, Any], client: Client) -> None:
        """Release the project metadata to make it publicly available in Syft.

        Args:
            metadata: Dictionary containing project metadata
            client: Syft client instance

        Raises:
            Exception: If metadata release fails
        """
        public_proj_path = (
            client.datasite_path / "public" / "llm_routers" / metadata["project_name"]
        )

        # Save metadata to the project path
        public_proj_path.mkdir(parents=True, exist_ok=True)
        metadata_path = public_proj_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))

    def publish(self) -> None:
        """Execute the publishing process.

        Raises:
            Abort: If any step in the publishing process fails
        """
        # Validate paths
        if not self.validate_paths():
            raise Abort()

        try:
            # Get project name from folder
            folder_path = self.config.folder.resolve()
            name = folder_path.name

            # Initialize client
            client = (
                Client.load(self.config.client_config)
                if self.config.client_config
                else Client.load()
            )

            # Get documented endpoints
            documented_endpoints = self.get_documented_endpoints(client, name)

            # Process tags
            tag_list = self.process_tags()

            # Generate metadata
            metadata_gen = ProjectMetadata(project_folder=folder_path)
            metadata = metadata_gen.generate(
                project_name=name,
                description=self.config.description,
                tags=tag_list,
                readme_content=self.get_readme_content(),
                documented_endpoints=documented_endpoints,
                pricing=self.config.pricing,
            )

            # Release metadata
            self.release_metadata(metadata, client)
            rprint(f"[green]✓ Successfully published {name}[/green]")

        except Exception as e:
            rprint(f"[red]Error during publishing: {str(e)}[/red]")
            raise Abort()


if __name__ == "__main__":
    publish_handler = PublishHandler(
        folder=Path("examples/rag-app"),
        description="RAG App",
        tags="llm,router,rag-app",
        readme=Path("examples/rag-app/README.md"),
        pricing_method=PricingMethod.PER_REQUEST,
        price=0.0001,
    )
    publish_handler.publish()
