import json
from pathlib import Path
from typing import Annotated, Optional, Union

from jinja2 import Template
from typer import Option, Typer

from syft_llm_router.publish_utils import ProjectMetadata, release_metadata

app = Typer(
    name="syftrouter",
    help="Syft LLM Router CLI",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=True,
)

TEMPLATE_FOLDER = Path(__file__).parent / "templates"

# Template filenames
TEMPLATE_FILES = [
    "server.py.tmpl",
    "router.py.tmpl",
    "pyproject.toml.tmpl",
    "chat_test.py.tmpl",
    "run.sh.tmpl",
]

# Add this with other constants
RPC_SCHEMA_FILENAME = Path("rpc.schema.json")
RPC_SCHEMA_PATH = "rpc" / RPC_SCHEMA_FILENAME

PROJECT_NAME_OPTS = Option(
    "--name",
    "-n",
    help="Name of the LLM Provider project",
)

PROJECT_DIR_OPTS = Option(
    "-f",
    "--folder",
    help="Path to a LLM Provider project folder",
)

DESCRIPTION_OPTS = Option(
    "-d",
    "--description",
    help="Project description",
)

TAGS_OPTS = Option(
    "-t",
    "--tags",
    help="Comma-separated list of tags",
)

README_OPTS = Option(
    "-r",
    "--readme",
    help="Path to README file",
)

DEFAULT_PROJECT_FOLDER = Path.cwd()


def __to_hyphenated(name: str) -> str:
    """Convert a name to a hyphenated string."""
    return "-".join(word.lower() for word in name.split())


def __copy_template(template_name: str, project_folder: Path) -> None:
    """
    Copy a template file to the project folder and replace placeholders."""

    dest_name = template_name.replace(".tmpl", "")

    src = TEMPLATE_FOLDER / template_name
    dest = project_folder / dest_name

    # Check if the template file exists
    if not src.exists():
        print(f"Template file {src} does not exist.")
        return

    # Read the template content
    raw_template = src.read_text()
    template = Template(raw_template)
    content = template.render(project_name=project_folder.name)

    # Replace placeholders in the template content
    dest.write_text(content)

    print(f"Created {dest_name} template at {dest}")


def __create_folder(folder: Union[str, Path]) -> Path:
    """
    Create a folder if it doesn't exist.
    """
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {folder}")
    return folder_path


@app.command()
def version() -> None:
    """Print syft_llm_router version."""
    from syft_llm_router import __version__

    print("Version: ", __version__)


@app.command()
def create_llmrouter_app(
    name: Annotated[str, PROJECT_NAME_OPTS] = "",
    folder: Annotated[Path, PROJECT_DIR_OPTS] = DEFAULT_PROJECT_FOLDER,
) -> None:
    """Initialize a new project in the given folder."""

    name = __to_hyphenated(name)

    # Create project folder if it doesn't exist
    project_folder = __create_folder(folder / name)

    # Copy the templates to the project folder
    for filename in TEMPLATE_FILES:
        __copy_template(filename, project_folder)

    print(f"Initialized project in {project_folder}")


@app.command()
def publish(
    folder: Annotated[Path, PROJECT_DIR_OPTS],
    description: Annotated[str, DESCRIPTION_OPTS],
    tags: Annotated[str, TAGS_OPTS],
    readme: Annotated[Path, README_OPTS],
    client_config: Annotated[
        Optional[Path], Option(help="Path to Syft client config file")
    ] = None,
) -> None:
    """Release project metadata to make it publicly available in Syft."""
    from syft_core import Client

    # project name is the folder name
    name = folder.name

    # Validate required files
    metadata_gen = ProjectMetadata(project_folder=folder)
    if not metadata_gen.validate_project_structure():
        print("Error: Invalid project structure")
        return

    # Read README content if provided
    readme_content = ""
    if readme and readme.exists():
        readme_content = readme.read_text()
    else:
        print("Warning: No README file provided")

    client = Client.load(client_config) if client_config else Client.load()

    documented_endpoints = {}
    # Load the RPC schema
    app_name = f"llm/{name}"
    rpc_schema_path = client.app_data(app_name) / RPC_SCHEMA_PATH
    # Validate the RPC schema exists
    if rpc_schema_path.exists():
        documented_endpoints = json.loads(rpc_schema_path.read_text())
    else:
        print(f"Error: RPC schema file does not exist at: {rpc_schema_path}")

    # Convert tags string to list
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

    # Generate metadata
    try:
        metadata = metadata_gen.generate(
            project_name=name,
            description=description or f"{name} LLM Router Implementation",
            tags=tag_list,
            readme_content=readme_content,
            documented_endpoints=documented_endpoints,
        )
    except Exception as e:
        print(f"Error generating metadata: {str(e)}")
        return

    # Release metadata
    if release_metadata(metadata, client):
        print(f"Successfully released metadata for {name}")
    else:
        print("Error releasing metadata")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
