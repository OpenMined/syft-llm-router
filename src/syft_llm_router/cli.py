from pathlib import Path
from typing import Annotated, Optional, Union

from jinja2 import Template
from loguru import logger
from typer import Abort, Option, Typer, confirm, prompt

from syft_llm_router.publish import PublishHandler

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
        logger.error(f"Template file {src} does not exist.")
        return

    # Read the template content
    raw_template = src.read_text()
    template = Template(raw_template)
    content = template.render(project_name=project_folder.name)

    # Replace placeholders in the template content
    dest.write_text(content)

    logger.info(f"Created {dest_name} template at {dest}")


def __create_folder(folder: Union[str, Path]) -> Path:
    """
    Create a folder if it doesn't exist.
    """
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created folder: {folder}")
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

    logger.success(f"Initialized project in {project_folder}")


@app.command()
def publish(
    folder: Annotated[
        Optional[Path],
        PROJECT_DIR_OPTS,
    ] = None,
    description: Annotated[Optional[str], DESCRIPTION_OPTS] = None,
    tags: Annotated[Optional[str], TAGS_OPTS] = None,
    readme: Annotated[
        Optional[Path],
        README_OPTS,
    ] = None,
    client_config: Annotated[
        Optional[Path], Option(help="Path to Syft client config file")
    ] = None,
) -> None:
    """Release project metadata to make it publicly available in Syft."""

    # If any required argument is not provided, prompt for it
    if folder is None:
        folder = prompt("Enter project directory path", type=Path)

    if description is None:
        description = prompt("Enter project description", type=str)

    if tags is None:
        tags = prompt("Enter project tags (comma-separated)", type=str)

    if readme is None:
        readme = prompt("Enter path to README file", type=Path)

    # Optional confirmation
    if not confirm("Do you want to proceed with publishing?"):
        raise Abort()

    # Create and execute publish handler
    handler = PublishHandler(
        folder=folder,
        description=description,
        tags=tags,
        readme=readme,
        client_config=client_config,
    )
    handler.publish()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
