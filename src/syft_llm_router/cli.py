from pathlib import Path
from typing import Annotated, Union

from typer import Option, Typer

app = Typer(
    name="syftrouter",
    help="Syft LLM Router CLI",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=True,
)


@app.command()
def version() -> None:
    """Print syft_llm_router version."""
    from syft_llm_router import __version__

    print("Version: ", __version__)


TEMPLATE_FOLDER = Path(__file__).parent / "templates"
SERVER_TEMPLATE_FILENAME = "server.py.tmpl"
PROVIDER_TEMPLATE_FILENAME = "router.py.tmpl"


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
    content = src.read_text()

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
def create_llmrouter_app(
    name: Annotated[str, PROJECT_NAME_OPTS],
    folder: Annotated[Path, PROJECT_DIR_OPTS] = Path.cwd(),
) -> None:
    """Initialize a new project in the given folder."""

    # Create project folder if it doesn't exist
    project_folder = __create_folder(folder / name)

    # Copy the templates to the project folder
    for filename in [SERVER_TEMPLATE_FILENAME, PROVIDER_TEMPLATE_FILENAME]:
        __copy_template(filename, project_folder)

    print(f"Initialized project in {project_folder}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
