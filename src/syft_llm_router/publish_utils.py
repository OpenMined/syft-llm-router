import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Union

import tomllib
from loguru import logger
from syft_core import Client


class ProjectMetadata:
    """Handles metadata generation and validation for LLM Router implementations."""

    def __init__(self, project_folder: Union[str, Path]) -> None:
        """Initialize the metadata generator with the project folder path.

        Args:
            project_folder: Path to the project directory containing the implementation.
        """
        self.project_folder = Path(project_folder)
        self.required_files = ["router.py", "server.py", "pyproject.toml", "run.sh"]

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
            logger.error(f"Missing required files: {', '.join(missing_files)}")
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
                logger.error(f"Error reading {file}: {str(e)}")
                raise

        return hasher.hexdigest()

    def read_project_metadata(self) -> dict:
        """Read and parse metadata from pyproject.toml.

        Returns:
            Dict: Parsed TOML content or empty dict if file doesn't exist.
        """
        toml_path = self.project_folder / "pyproject.toml"
        if not toml_path.exists():
            logger.warning("pyproject.toml not found")
            return {}

        try:
            return tomllib.loads(toml_path.read_text())
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {str(e)}")
            return {}

    def generate(
        self,
        project_name: str,
        description: str,
        tags: list[str],
        readme_content: str,
        documented_endpoints: dict,
    ) -> dict:
        """Generate metadata dictionary with all project information.

        Args:
            project_name: Name of the project
            description: Project description
            tags: List of tags for categorization
            readme_content: Content of the README file
            documented_endpoints: List of documented endpoints with their descriptions

        Returns:
            Dict: Complete metadata dictionary
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
        }


def release_metadata(metadata: dict, client: Client) -> bool:
    """Release the project metadata to make it publicly available in Syft.

    Args:
        metadata: Dictionary containing project metadata
        client: Syft client instance

    Returns:
        bool: True if successful, False otherwise
    """
    public_proj_path = (
        client.datasite_path / "public" / "llm_routers" / metadata["project_name"]
    )

    # Save metadata to the project path
    public_proj_path.mkdir(parents=True, exist_ok=True)
    metadata_path = public_proj_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    return True


if __name__ == "__main__":
    # Example usage
    project_folder = Path("examples/phi3")

    # Example documented endpoints
    endpoints = {
        "/chat": {
            "method": "POST",
            "description": "Chat completion endpoint for the LLM",
            "parameters": {
                "messages": "List of chat messages",
                "model": "Model to use for completion",
            },
        }
    }

    # Generate metadata
    metadata_gen = ProjectMetadata(project_folder=project_folder)
    metadata = metadata_gen.generate(
        project_name="phi3",
        description="Phi3 LLM Router Implementation",
        tags=["llm", "router", "phi3"],
        readme_content="# Phi3 Router\n\nOverview...",
        documented_endpoints=endpoints,
    )

    print("Metadata generated successfully")
    print(metadata)

    # Release metadata
    client = Client.load()
    release_metadata(metadata, client)
