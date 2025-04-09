# OpenAI based SyftLLM Router

## Navigate to the OpenAI Example

```bash
cd examples/openai
```

## Install Dependencies

First, ensure you have [uv](https://github.com/astral-sh/uv) installed. Then:

```bash
uv venv

uv sync
```

## Start the Server

Once dependencies are installed, launch the server:

```bash
uv run python server.py
```
## Test the Server

First, ensure the server is running, then execute:

```bash
uv run python chat_request
```
