# Syft LLM Router

A simple router for Language Model applications built over SyftBox. This tool allows you to create, deploy, and share LLM routers that can be accessed through SyftBox.

## Installation

1. Install [uv](https://github.com/astral-sh/uv) (Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/OpenMined/syft-llm-router.git
cd syft-llm-router
```

3. Create a virtual environment and install dependencies:
```bash
uv sync -P syft-llm-router
```

## Quick Start

1. Create a new router application:
```bash
uv run syftllm create-router-app -n my-llm-router
cd my-llm-router
```
This creates a new directory with the basic router structure.

2. Implement your router logic in `my-llm-router/router.py`:
   - Define your LLM provider
   - Implement chat and completion endpoints
   - Add any custom functionality

3. Configure the server in `my-llm-router/server.py`:
   - Import your router implementation
   - Set up the SyftEvents server
   - Configure any required parameters

4. Install additional dependencies:
   - Add any required packages to `pyproject.toml`
   - Run `uv sync` to install them

5. Start the router server:
```bash
cd my-llm-router
uv run python server.py --project-name llm-router --api-key YOUR_API_KEY
```
This starts an RPC server over SyftBox that handles LLM requests.

## Examples

The [examples](./examples) folder contains complete implementations for different LLM providers:
- [Phi-4 Router](./examples/phi4router) - Implementation using Microsoft's Phi-4 model
- [Mixtral Router](./examples/mixtral) - Implementation using Mixtral-8x22b-instruct model

Each example includes:
- Router implementation
- Server configuration
- Test scripts
- Documentation

## Publishing Your Router

For instructions on how to publish your router to make it available to other users through your datasite's public folder, please see the [Publishing Guide](./publish.md).
