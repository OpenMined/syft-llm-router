# Phi-4 LLM Router Example

This example demonstrates how to create a Syft LLM Router for the Microsoft Phi-4 model using the OpenRouter API. The example includes a complete implementation of a router server and client testing code.

## Overview

The example consists of three main components:
1. `router.py` - Implements the Phi-4 LLM Router using the OpenRouter API
2. `server.py` - Sets up the SyftEvents server to handle LLM requests
3. `chat_test.py` - Provides example code for testing both chat and completion endpoints

## Prerequisites

- Python 3.9 or higher
- OpenRouter API key
- SyftBox client configuration
- Required Python packages (installed via `uv`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/OpenMined/syft-llm-router.git
cd syft-llm-router/examples/phi4router
```

2. Create environment and Install dependencies:
```bash
uv sync
```

## Configuration

1. Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

2. Ensure your SyftBox client is properly configured and running.

## Running the Example

1. Start the router server:
```bash
uv run python server.py --project-name phi4router --api-key $OPENROUTER_API_KEY
```

2. In a separate terminal, run the test script:
```bash
uv run python chat_test.py
```

## Features

- **Chat Completion**: Supports chat-based interactions with the Phi-4 model
- **Text Completion**: Supports text completion requests
- **Configurable Options**: Supports various generation parameters like temperature, max_tokens, and top_p
- **Logprobs Support**: Includes token-level probability information
- **Error Handling**: Comprehensive error handling and logging
- **Logging**: Detailed logging using loguru

## API Endpoints

The server exposes the following endpoints:
- `/chat` - For chat completion requests
- `/completions` - For text completion requests
- `/ping` - For health checks

## Example Usage

The `chat_test.py` file includes examples of both chat and completion requests:

```python
# Chat example
response = test_chat(
    client=client,
    datasite=datasite,
    user_message="How many legs does a spider have?",
    system_message="Limit your answer to the final result. Explain your answer.",
    model="phi-4"
)

# Completion example
response = test_completion(
    client=client,
    datasite=datasite,
    prompt="What is 1+1?",
    model="phi-4"
)
```

## Error Handling

The router includes comprehensive error handling for:
- Invalid API keys
- Model validation
- API request failures
- Response parsing errors
