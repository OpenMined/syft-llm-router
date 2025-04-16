# Syft LLM Router

A simple router for Language Model applications built over SyftBox.

## Installation

1. First, ensure you have [uv](https://github.com/astral-sh/uv) installed.


2. Clone the repo

```bash
git clone https://github.com/OpenMined/syft-llm-router.git
cd syft-llm-router
```

3. Create environment and install dependencies

```bash
uv sync -P syft-llm-router
```

## Quick Start

1. Create a new router application:

```bash
uv run syftllm create-router-app -n my-llm-router
```

2. Implement the router server in `my-llm-router/router.py`

3. Import and load the router in `my-llm-router/server.py`

4. Install any dependencies required by your router

5. Start the router server

This start an RPC server over SyftBox.

```bash
uv run python my-llm-router/server.py --project-name llm-router
```

## Examples

Please refer to the examples in the [examples](./examples) folder for detailed sample router implementations.

## Publishing Your Router

For instructions on how to publish your router to make it available to other users through your datasite's public folder, please see the [Publishing Guide](./publish.md).
