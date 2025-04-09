# Syft LLM Router

A simple router for Language Model applications built over SyftBox.

## Installation

First, ensure you have [uv](https://github.com/astral-sh/uv) installed. Then:

```bash
uv venv

uv pip install syft-llm-router
```

## Quick Start

1. Create a new router application:

```bash
uv run syftllm create-router-app -n openai-router
```

2. Implement the router server in `openai-router/router.py`

3. Import and load the router in `openai-router/server.py`

4. Install any dependencies required by your router

5. Start the router server:

This start an RPC server over SyftBox.

```bash
uv run python openai-router/server.py
```

## Examples

Please refer to the examples in the [examples](./examples) folder for sample router implementations.
