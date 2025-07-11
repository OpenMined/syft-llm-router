#!/usr/bin/env python3
"""Simplified project generator for Syft LLM Router with two paths: default and custom."""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, field_validator
from syft_core.config import SyftClientConfig

RouterType = Literal["default", "custom"]


class ProjectConfig(BaseModel):
    """Simplified configuration for project generation."""

    project_name: str
    router_type: RouterType
    enable_chat: bool = True
    enable_search: bool = True
    syftbox_config: SyftClientConfig

    # add a pydantic validator to format the project name
    # Replace spaces by dashes and convert to lowercase
    # Remove leading and trailing spaces
    @field_validator("project_name", mode="before")
    def validate_project_name(cls, v):
        return v.strip().replace(" ", "-").lower()


class SimplifiedProjectGenerator:
    """Generates router projects with two distinct paths: default or custom."""

    def __init__(self, template_dir: str = "."):
        """Initialize the generator with template directory."""
        self.template_dir = Path(template_dir)
        self.common_dir = self.template_dir / "common"
        self.templates_dir = self.template_dir / "templates"

    def generate_project(self, config: ProjectConfig, output_dir: str) -> None:
        """Generate a complete router project based on configuration."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"🚀 Generating {config.router_type} router: {config.project_name}")

        # Copy common files (shared layer)
        self._copy_common_files(output_path)

        # Copy template-specific files
        template_path = self.templates_dir / config.router_type
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")

        self._copy_template_files(output_path, template_path, config)

        # Generate deployment scripts
        self._generate_deployment_scripts(output_path, config)

        # Generate validation script
        self._generate_validation_script(output_path, config)

        print(f"✅ Project generated successfully in: {output_dir}")

    def _copy_common_files(self, output_path: Path) -> None:
        """Copy common files that are shared between all router types."""
        common_files = ["base_services.py", "schema.py", "server.py"]

        for file_name in common_files:
            source = self.common_dir / file_name
            if source.exists():
                shutil.copy2(source, output_path / file_name)
                print(f"✅ Copied {file_name}")
            else:
                print(f"⚠️  Common file not found: {source}")

    def _copy_template_files(
        self, output_path: Path, template_path: Path, config: ProjectConfig
    ) -> None:
        """Copy template-specific files based on router type."""
        # Copy all files from template directory
        for item in template_path.rglob("*"):
            if item.is_file():
                # Calculate relative path from template directory
                relative_path = item.relative_to(template_path)
                target_path = output_path / relative_path

                # Create target directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(item, target_path)
                print(f"✅ Copied {relative_path}")

        # Generate router.py based on template
        self._generate_router(output_path, config)

        # Generate requirements.txt
        self._generate_requirements(output_path, config)

        # Generate .env.example
        self._generate_env_example(output_path, config)

        # Generate README.md
        self._generate_readme(output_path, config)

    def _generate_router(self, output_path: Path, config: ProjectConfig) -> None:
        """Generate router.py with factory pattern."""
        router_content = f'''"""Router implementation for {config.project_name}."""

from typing import List, Optional
from uuid import UUID

from schema import (
    ChatResponse,
    GenerationOptions,
    Message,
    SearchOptions,
    SearchResponse,
)

from base_services import ChatService, SearchService
from config import load_config


class RouterFactory:
    """Factory for creating service instances based on configuration."""
    
    @staticmethod
    def create_chat_service() -> ChatService:
        """Create chat service instance."""
        try:
            from chat_service import ChatServiceImpl
            return ChatServiceImpl()
        except ImportError:
            raise ImportError("Chat service implementation not found")
    
    @staticmethod
    def create_search_service() -> SearchService:
        """Create search service instance."""
        try:
            from search_service import SearchServiceImpl
            return SearchServiceImpl()
        except ImportError:
            raise ImportError("Search service implementation not found")


class SyftLLMRouter:
    """Syft LLM Router that orchestrates chat and search services."""

    def __init__(self):
        """Initialize the router with configured services."""
        self.config = load_config()
        
        # Initialize services using factory pattern
        self.chat_service = None
        self.search_service = None
        
        if self.config.enable_chat:
            self.chat_service = RouterFactory.create_chat_service()
        
        if self.config.enable_search:
            self.search_service = RouterFactory.create_search_service()

    def generate_chat(
        self,
        model: str,
        messages: List[Message],
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response based on conversation history."""
        if not self.chat_service:
            raise NotImplementedError("Chat functionality is not enabled")
        return self.chat_service.generate_chat(model, messages, options)

    def search_documents(
        self,
        query: str,
        options: Optional[SearchOptions] = None,
    ) -> SearchResponse:
        """Search documents from the index based on a search query."""
        if not self.search_service:
            raise NotImplementedError("Search functionality is not enabled")
        return self.search_service.search_documents(query, options)
'''

        with open(output_path / "router.py", "w") as f:
            f.write(router_content)

    def _generate_requirements(self, output_path: Path, config: ProjectConfig) -> None:
        """Generate pyproject.toml with optional dependency groups."""
        pyproject_content = f"""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{config.project_name}"
version = "0.1.0"
description = "A Syft LLM Router with configurable chat and search services"
authors = [
    {{name = "{config.syftbox_config.email}"}}
]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "syft-core>=0.2.7",
    "fastsyftbox>=0.1.18",
    "pydantic>=2.0.0",
    "loguru>=0.7.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "typing-extensions>=4.0.0",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
]

[project.optional-dependencies]
chat = [
    "aiohttp>=3.8.0",
]
search = [
    "httpx>=0.24.0",
]
all = [
    "aiohttp>=3.8.0",
    "httpx>=0.24.0",
]

[tool.setuptools.packages.find]
where = ["."]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
"""

        with open(output_path / "pyproject.toml", "w") as f:
            f.write(pyproject_content)

    def _generate_env_example(self, output_path: Path, config: ProjectConfig) -> None:
        """Generate .env.example file."""
        env_vars = [
            "# Router Configuration",
            f"PROJECT_NAME={config.project_name}",
            "",
            "# Service Configuration",
            f"ENABLE_CHAT={str(config.enable_chat).lower()}",
            f"ENABLE_SEARCH={str(config.enable_search).lower()}",
            "",
        ]

        if config.router_type == "default":
            env_vars.extend(
                [
                    "# Default Router Configuration",
                    "OLLAMA_BASE_URL=http://localhost:11434",
                    "RAG_SERVICE_URL=http://localhost:9000",
                ]
            )
        else:  # custom
            env_vars.extend(
                [
                    "# Custom Router Configuration",
                    "# Add your custom configuration here",
                    "# CUSTOM_CHAT_API_KEY=your_api_key",
                    "# CUSTOM_CHAT_BASE_URL=your_base_url",
                    "# CUSTOM_SEARCH_API_KEY=your_api_key",
                    "# CUSTOM_SEARCH_BASE_URL=your_base_url",
                ]
            )

        with open(output_path / ".env.example", "w") as f:
            f.write("\n".join(env_vars) + "\n")

    def _generate_readme(self, output_path: Path, config: ProjectConfig) -> None:
        """Generate README.md."""
        if config.router_type == "default":
            # Determine which services are enabled for the README
            enabled_services = []
            if config.enable_chat:
                enabled_services.append("Chat (Ollama)")
            if config.enable_search:
                enabled_services.append("Search (Local RAG)")

            services_text = ", ".join(enabled_services) if enabled_services else "None"

            readme_content = f"""# {config.project_name}

A Syft LLM Router with default implementations for chat (Ollama) and search (Local RAG).

## Features

- ✅ **Chat Service**: Ollama integration for local LLM chat
- ✅ **Search Service**: Local RAG for document retrieval
- ✅ **FastAPI Server**: RESTful API endpoints
- ✅ **Health Monitoring**: Built-in health checks
- ✅ **Validation**: Automated testing and validation

## Enabled Services

This router has the following services enabled: **{services_text}**

## Quick Start

**Start the router**:
```bash
./run.sh
```

The script will automatically handle setup and start the router.

3. **Test**:
   ```bash
   python validate.py
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat completion (if enabled)
- `POST /search` - Document search (if enabled)

## Configuration

Edit `.env` file to customize:
- Ollama base URL
- RAG service url
- Service enablement

## Dependency Management

This project uses `pyproject.toml` with optional dependencies:

### Base Dependencies (Always Installed)
- FastAPI, Uvicorn, Pydantic, etc.

### Optional Dependencies
- **Chat Service**: `pip install -e .[chat]`
- **Search Service**: `pip install -e .[search]`
- **All Services**: `pip install -e .[all]`

### Adding Services Later
To enable additional services after setup:

```bash
# Enable chat service
pip install -e .[chat]

# Enable search service  
pip install -e .[search]

# Enable both services
pip install -e .[all]
```

## Requirements

- Python 3.9+
- Ollama (for chat service)
- 4GB+ RAM (for local models)
"""
        else:  # custom
            readme_content = f"""# {config.project_name}

A custom Syft LLM Router template. Implement your own chat and search services.

## Features

- 🔧 **Custom Chat Service**: Implement your own chat logic
- 🔧 **Custom Search Service**: Implement your own RAG logic
- ✅ **FastAPI Server**: RESTful API endpoints
- ✅ **Health Monitoring**: Built-in health checks
- ✅ **Validation**: Automated testing and validation

## Implementation

1. **Edit `chat_service.py`**: Implement your chat service
2. **Edit `search_service.py`**: Implement your search service
3. **Edit `config.py`**: Add your configuration options
4. **Update `.env`**: Configure your environment variables
5. **Add dependencies**: Update `pyproject.toml` with your service dependencies

## Quick Start

1. **Start the router**:
   ```bash
   ./run.sh
   ```

2. **Implement Services**: Edit the service files

The script will automatically handle setup and start the router.

4. **Test**:
   ```bash
   python validate.py
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat completion
- `POST /search` - Document retrieval

## Dependency Management

This project uses `pyproject.toml` for dependency management:

1. **Add your dependencies** to `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   my-service = [
       "your-dependency>=1.0.0",
   ]
   ```

2. **Install with your dependencies**:
   ```bash
   pip install -e .[my-service]
   ```

## Requirements

- Python 3.9+
- Your custom dependencies (add to pyproject.toml)
"""

        with open(output_path / "README.md", "w") as f:
            f.write(readme_content)

    def _generate_deployment_scripts(
        self, output_path: Path, config: ProjectConfig
    ) -> None:
        """Generate deployment scripts."""
        self._generate_run_script(output_path, config)

    def _generate_run_script(self, output_path: Path, config: ProjectConfig) -> None:
        """Generate intelligent run.sh script with integrated setup."""
        if config.router_type == "default":
            # Determine which optional dependencies to install
            extras = []
            if config.enable_chat:
                extras.append("chat")
            if config.enable_search:
                extras.append("search")

            if extras:
                install_command = f"pip install -e .[{','.join(extras)}]"
                extras_info = f" with extras: {', '.join(extras)}"
            else:
                install_command = "pip install -e ."
                extras_info = " (base dependencies only)"

            run_script_content = f"""#!/bin/bash
set -e

# {config.project_name} Router Startup Script (Default)
# Generated automatically - includes setup every time

echo "🚀 Starting {config.project_name} router..."

# Setup phase (runs every time for consistency)
echo "🔧 Running setup..."

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies{extras_info}
echo "📥 Installing/updating dependencies..."
pip install --upgrade pip
{install_command}

# Copy environment file if missing
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Created .env file from template. Please edit with your configuration."
fi

# Service-specific setup based on enabled services
{self._generate_conditional_setup_commands(config)}

echo "✅ Setup complete!"

# Start the router
echo "🎯 Starting router server..."
python server.py --project-name {config.project_name}

deactivate
"""
        else:  # custom
            run_script_content = f"""#!/bin/bash
set -e

# {config.project_name} Router Startup Script (Custom)
# Generated automatically - includes setup every time

echo "🚀 Starting {config.project_name} router..."

# Setup phase (runs every time for consistency)
echo "🔧 Running setup..."

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "📥 Installing/updating dependencies..."
pip install --upgrade pip
pip install -e .

# Copy environment file if missing
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Created .env file from template. Please edit with your configuration."
fi

echo "✅ Setup complete!"

# Start the router
echo "🎯 Starting router server..."
python server.py --project-name {config.project_name}

deactivate
"""

        run_script_path = output_path / "run.sh"
        with open(run_script_path, "w") as f:
            f.write(run_script_content)
        run_script_path.chmod(0o755)

    def _generate_conditional_setup_commands(self, config: ProjectConfig) -> str:
        """Generate conditional setup commands based on enabled services."""
        setup_commands = []

        if config.enable_chat:
            setup_commands.append(
                """
# Ollama setup (for chat service)
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Please install Ollama first:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   Then run: ollama pull tinyllama"
    exit 1
fi

# Check if required model is available
if ! ollama list | grep -q "tinyllama"; then
    echo "📥 Pulling tinyllama model..."
    ollama pull tinyllama  
fi
"""
            )

        if config.enable_search:
            setup_commands.append(
                f"""
# Local RAG setup (for search service)
echo "🔍 Setting up local RAG components..."


# Install local-rag using syftbox


# Check if local-rag is already installed   
if ! syftbox app list -c {config.syftbox_config.path} | grep -q "local-rag"; then
    echo "📥 Installing local-rag..."
    SYFTBOX_ASSIGNED_PORT=9083 syftbox app install https://github.com/OpenMined/local-rag --config {config.syftbox_config.path}
fi

export RAG_URL=http://localhost:9083
"""
            )

        if not setup_commands:
            setup_commands.append(
                """
# No services enabled - skipping service-specific setup
echo "ℹ️  No services enabled - skipping service-specific setup"
"""
            )

        return "\n".join(setup_commands)

    def _generate_validation_script(
        self, output_path: Path, config: ProjectConfig
    ) -> None:
        """Generate validation script."""
        # Determine which tests to run based on enabled services
        tests_to_run = ["test_router_health"]

        if config.enable_chat:
            tests_to_run.append("test_chat_endpoint")

        if config.enable_search:
            tests_to_run.append("test_search_endpoint")

        validation_script_content = f"""#!/usr/bin/env python3
\"\"\"
{config.project_name} Router Validation Script
Tests the generated router to ensure it works correctly.
\"\"\"

import sys
import time
import requests

def test_router_health():
    \"\"\"Test router health endpoint.\"\"\"
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {{response.status_code}}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {{e}}")
        return False

def test_chat_endpoint():
    \"\"\"Test chat endpoint if enabled.\"\"\"
    try:
        payload = {{
            "model": "test-model",
            "messages": [
                {{"role": "user", "content": "Hello, how are you?"}}
            ]
        }}
        response = requests.post("http://localhost:8000/chat", json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Chat endpoint test passed")
            return True
        else:
            print(f"❌ Chat endpoint test failed: {{response.status_code}}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat endpoint test failed: {{e}}")
        return False

def test_search_endpoint():
    \"\"\"Test search endpoint if enabled.\"\"\"
    try:
        payload = {{
            "query": "test query",
            "options": {{"limit": 5}}
        }}
        response = requests.post("http://localhost:8000/search", json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Search endpoint test passed")
            return True
        else:
            print(f"❌ Search endpoint test failed: {{response.status_code}}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Search endpoint test failed: {{e}}")
        return False

def main():
    \"\"\"Run validation tests.\"\"\"
    print(f"🧪 Testing {{config.project_name}} router...")
    print(f"🔧 Enabled services: Chat={{config.enable_chat}}, Search={{config.enable_search}}")
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Define test functions
    test_functions = {{
        "test_router_health": test_router_health,
        "test_chat_endpoint": test_chat_endpoint,
        "test_search_endpoint": test_search_endpoint
    }}
    
    # Run only enabled tests
    tests = [test_functions[test_name] for test_name in {tests_to_run}]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\\n📊 Test Results: {{passed}}/{{total}} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Router is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the router configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""

        validation_script_path = output_path / "validate.py"
        with open(validation_script_path, "w") as f:
            f.write(validation_script_content)
        validation_script_path.chmod(0o755)


def main():
    """Main entry point for the generator."""
    parser = argparse.ArgumentParser(
        description="Generate a Syft LLM Router project (default or custom)"
    )

    parser.add_argument(
        "--project-name", type=str, required=True, help="Name of the project"
    )

    parser.add_argument(
        "--router-type",
        type=str,
        choices=["default", "custom"],
        default="default",
        help="Type of router to generate (default: default)",
    )

    parser.add_argument(
        "--disable-chat",
        action="store_true",
        help="Disable chat service (default: enabled)",
    )

    parser.add_argument(
        "--disable-search",
        action="store_true",
        help="Disable search service (default: enabled)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for generated project (default: ./generated_router)",
        default="./generated_router",
    )

    parser.add_argument(
        "--template-dir",
        type=str,
        help="Template directory (default: current directory)",
        default=".",
    )

    parser.add_argument(
        "--syftbox-config",
        type=str,
        help="SyftBox config file (default: ./syftbox_config.json)",
        default="~/.syftbox/config.json",
    )

    args = parser.parse_args()

    try:
        # Handle disable flags (they override default True)
        enable_chat = not args.disable_chat
        enable_search = not args.disable_search

        # Create SyftBox configuration
        syftbox_config = SyftClientConfig.load(args.syftbox_config)

        # Create configuration
        config = ProjectConfig(
            project_name=args.project_name,
            router_type=args.router_type,
            enable_chat=enable_chat,
            enable_search=enable_search,
            syftbox_config=syftbox_config,
        )

        # Initialize generator
        template_dir = Path(args.template_dir)
        if not template_dir.exists():
            print(f"Error: Template directory not found: {template_dir}")
            sys.exit(1)

        generator = SimplifiedProjectGenerator(template_dir)

        # Generate project
        generator.generate_project(config, args.output_dir)

        print(f"\\n🎉 Project generated successfully!")
        print(f"📁 Location: {args.output_dir}")
        print(f"🔧 Type: {config.router_type}")
        print(f"💬 Chat: {'✅' if config.enable_chat else '❌'}")
        print(f"🔍 Search: {'✅' if config.enable_search else '❌'}")

        print(f"\\n🚀 Next steps:")
        print(f"  cd {args.output_dir}")
        print(f"  ./run.sh")

    except Exception as e:
        print(f"Generation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
