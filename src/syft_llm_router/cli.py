import json
import subprocess
import time
import platform
from pathlib import Path
from typing import Annotated, Optional, Union

from jinja2 import Template
from typer import Option, Typer

from syft_llm_router.publish_utils import ProjectMetadata, release_metadata

app = Typer(
    name="syft-router",
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
def create_app(
    name: Annotated[str, PROJECT_NAME_OPTS] = "",
    folder: Annotated[Path, PROJECT_DIR_OPTS] = DEFAULT_PROJECT_FOLDER,
    dir_path: Annotated[
        Optional[Path],
        Option(
            "--dir", 
            "-d",
            help="Target directory to create the project in (alternative to --folder)"
        )
    ] = None,
) -> None:
    """Initialize a new project in the given folder."""

    target_folder = dir_path 
    
    name = __to_hyphenated(name)

    # Create project folder if it doesn't exist
    project_folder = __create_folder(target_folder / name)

    # Copy the templates to the project folder
    for filename in TEMPLATE_FILES:
        __copy_template(filename, project_folder)

    print(f"Initialized project in {project_folder}")


@app.command()
def publish(
    description: Annotated[
        Optional[str], 
        DESCRIPTION_OPTS
    ] = None,
    tags: Annotated[
        Optional[str], 
        TAGS_OPTS
    ] = None,
    readme: Annotated[
        Optional[Path], 
        README_OPTS
    ] = None,
    client_config: Annotated[
        Optional[Path], Option(help="Path to Syft client config file")
    ] = None,
    dir_path: Annotated[
        Path,
        Option(
            "--dir", 
            "-d",
            help="Target directory containing the project"
        )
    ] = None,
) -> None:
    """Release project metadata to make it publicly available in Syft."""
    if not dir_path:
        print("Error: --dir parameter is required")
        return
    target_folder = dir_path
    
    from syft_core import Client

    # project name is the folder name
    name = target_folder.name
    
    if description is None:
        description = input(f"Enter a description for {name} [default: '{name} LLM Router Implementation']: ")
        description = description.strip()
        if not description:
            description = f"{name} LLM Router Implementation"
    
    if tags is None:
        tags = input("Enter comma-separated tags (e.g., 'imaging,medical,multimodal'): ")
        
    readme_content = ""
    if readme is None:
        readme_path = input(f"Enter path to README file [default: {target_folder}/README.md]: ")
        readme_path = readme_path.strip()
        
        if not readme_path:
            readme_path = target_folder / "README.md"
        else:
            readme_path = Path(readme_path)
                

    # Validate required files
    metadata_gen = ProjectMetadata(project_folder=target_folder)
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
            description=description,
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


def __install_dependencies(target_folder: Path) -> bool:
    """Install dependencies for a project, with fallback options."""
    print("Installing dependencies...")
    
    try:
        subprocess.run(
            "uv sync --project . --quiet",
            shell=True,
            cwd=target_folder,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print("\nDependency installation failed.")
        return False


@app.command()
def test_app(
    server_args: Annotated[
        Optional[list[str]], 
        Option(
            "--server-arg", 
            "-s", 
            help="Additional arguments to pass to the server (can be used multiple times, e.g. -s '--project-name my-llm' -s '--api-key MY_KEY')"
        )
    ] = None,
    dir_path: Annotated[
        Optional[Path],
        Option(
            "--dir", 
            "-d",
            help="Target directory containing the project"
        )
    ] = DEFAULT_PROJECT_FOLDER,
    debug: Annotated[
        bool,
        Option(
            "--debug",
            help="Show server logs during execution"
        )
    ] = False,
) -> None:
    """Run the server and test script to verify the integration works correctly."""
    target_folder = dir_path
    
    try:
        __install_dependencies(target_folder)
        
        print("Starting server...")
        server_cmd = "uv run --quiet python server.py"
        if server_args:
            server_cmd += " " + " ".join(server_args)
            
        # Only show command details in debug mode
        if debug:
            print(f"Server command: {server_cmd}")
        
        # If debug mode is enabled, show server output directly
        if debug:
            server_process = subprocess.Popen(
                server_cmd,
                shell=True,
                cwd=target_folder,
            )
        else:
            with open("/dev/null", "w") as devnull:
                server_process = subprocess.Popen(
                    server_cmd,
                    shell=True,
                    cwd=target_folder,
                    stdout=devnull,
                    stderr=devnull,
                )
                
        time.sleep(5)

        if server_process.poll() is not None:
            print("Error: Server failed to start.")
            return
            
        print("\nStarting interactive chat test. Press Ctrl+C to exit.")
        print("You can now interact with the chatbot.\n")
        
        try:
            chat_process = subprocess.Popen(
                "uv run --quiet python chat_test.py",
                shell=True,
                cwd=target_folder,
            )
            
            # Keep the process running until user terminates
            chat_process.wait()
            
        except KeyboardInterrupt:
            print("\nChat test terminated by user.")
        finally:
            # Clean up the chat process
            if 'chat_process' in locals() and chat_process.poll() is None:
                chat_process.terminate()
                chat_process.wait()
                
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {str(e)}")
    finally:
        if 'server_process' in locals() and server_process.poll() is None:
            print("Shutting down server...")
            server_process.terminate()
            server_process.wait()


@app.command()
def serve(
    server_args: Annotated[
        Optional[list[str]], 
        Option(
            "--server-arg", 
            "-s", 
            help="Additional arguments to pass to the server (can be used multiple times, e.g. -s '--project-name my-llm' -s '--api-key MY_KEY')"
        )
    ] = None,
    dir_path: Annotated[
        Optional[Path],
        Option(
            "--dir", 
            "-d",
            help="Target directory containing the project"
        )
    ] = DEFAULT_PROJECT_FOLDER,
    debug: Annotated[
        bool,
        Option(
            "--debug",
            help="Show server logs during execution instead of writing to a log file"
        )
    ] = False,
) -> None:
    """Start the server in a detached process."""
    target_folder = dir_path
    
    try:
        __install_dependencies(target_folder)   

        server_cmd = "uv run --quiet python server.py"
        if server_args:
            server_cmd += " " + " ".join(server_args)
            
        # Only show command details in debug mode
        if debug:
            print(f"Server command: {server_cmd}")
        
        # In debug mode, don't detach and show logs directly
        if debug:
            print("Running server in debug mode with logs shown (Ctrl+C to stop)...")
            try:
                subprocess.run(
                    server_cmd,
                    shell=True,
                    cwd=target_folder,
                    check=True,
                )
            except KeyboardInterrupt:
                print("\nServer stopped by user.")
            return
            
        # For non-debug mode, use detached process with log file
        log_file = target_folder / "server.log"
        print(f"Server logs will be written to: {log_file}")
        
        with open(log_file, "w") as log:
            server_process = subprocess.Popen(
                server_cmd,
                shell=True,
                cwd=target_folder,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        
        time.sleep(2)
        if server_process.poll() is None:
            print(f"Server started successfully with PID {server_process.pid}!")
            print(f"The server will continue running in the background.")
        else:
            print("Error: Server failed to start. Check the log file for details.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {str(e)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
