# Claude LLM Router Example

This example demonstrates how to create a Syft LLM Router for Claude models using the Anthropic API. The example includes a complete implementation of a router server and client testing code, with integrated accounting functionality for transaction tracking and billing.

## Overview

The example consists of four main components:
1. `router.py` - Implements the Claude LLM Router using the Anthropic API
2. `server.py` - Sets up the SyftEvents server to handle LLM requests with accounting integration
3. `accounting.py` - Handles accounting client initialization and configuration
4. `chat_test.py` - Provides example code for testing both chat and completion endpoints with accounting tokens

## Prerequisites

- Python 3.9 or higher
- Anthropic API key
- SyftBox client configuration
- Accounting service URL (set via `ACCOUNTING_SERVICE_URL` environment variable)
- Required Python packages (installed via `uv`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/OpenMined/syft-llm-router.git
cd syft-llm-router/examples/claude
```

3. Create environment and Install dependencies:
```bash
uv sync
```

## Configuration

1. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

2. Set your accounting service URL (optional, will use default if not set):
```bash
export ACCOUNTING_SERVICE_URL="your-accounting-service-url"
```

3. Ensure your SyftBox client is properly configured and running.

## Running the Example

### Option 1: Using the run script
```bash
./run.sh
```

### Option 2: Manual execution
1. Start the router server:
```bash
uv run python server.py --project-name claude --api-key $ANTHROPIC_API_KEY
```

2. In a separate terminal, run the test script:
```bash
uv run python chat_test.py
```

## Features

- **Chat Completion**: Supports chat-based interactions with Claude models
- **Text Completion**: Supports text completion requests
- **Multiple Claude Models**: Supports Claude 3 Opus, Sonnet, and Haiku
- **Accounting Integration**: Automatic transaction tracking and billing for chat requests
- **Configurable Pricing**: Pricing per request configurable via `pyproject.toml`
- **Configurable Options**: Supports various generation parameters like temperature, max_tokens, and top_p
- **Error Handling**: Comprehensive error handling and logging
- **Logging**: Detailed logging using loguru

## Supported Models

The router supports the following Claude models:
- `claude-3-opus` - Claude 3 Opus (most capable)
- `claude-3-sonnet` - Claude 3 Sonnet (balanced)
- `claude-3-haiku` - Claude 3 Haiku (fastest)
- `claude` - Alias for Claude 3 Sonnet

## Accounting Functionality

The router includes integrated accounting functionality:

- **Transaction Tokens**: Each chat request requires an accounting token for billing
- **Automatic Billing**: Transactions are automatically created, confirmed, or cancelled based on request success
- **Configurable Pricing**: Pricing is set in `pyproject.toml` under `[tool.claude.pricing_per_request]`
- **Error Recovery**: Failed requests automatically cancel pending transactions

### Accounting Configuration

The accounting client is automatically initialized on first use. Configuration is stored in `~/.syftbox/accounting-config.json`.

## API Endpoints

The server exposes the following endpoints:
- `/chat` - For chat completion requests (requires accounting token)
- `/completions` - For text completion requests
- `/ping` - For health checks

## Example Usage

The `chat_test.py` file includes examples of both chat and completion requests:

```python
# Initialize accounting client
accounting_client = accounting.get_or_init_user_client()

# Chat example with accounting
response = test_chat(
    client=client,
    accounting_client=accounting_client,
    datasite=datasite,
    user_message="How many legs does a spider have?",
    system_message="Limit your answer to the final result. Explain your answer.",
    model="claude-3-sonnet"
)

# Completion example (no accounting required)
response = test_completion(
    client=client,
    datasite=datasite,
    prompt="What is 1+1?",
    model="claude-3-sonnet"
)
```

## API Differences from OpenAI

The Anthropic API has some differences from the OpenAI API:

1. **System Messages**: System messages are handled differently and may be skipped in some contexts
2. **Model Names**: Uses full model names with version suffixes
3. **Response Format**: Slightly different response structure
4. **Finish Reasons**: Different finish reason values (`end_turn`, `max_tokens`, `stop_sequence`)

## Error Handling

The router includes comprehensive error handling for:
- Invalid API keys
- Model validation
- API request failures
- Response parsing errors
- Accounting transaction failures

## Publishing your Router
For instructions on how to publish your router to make it available to other users through your datasite's public folder, please see the [Publishing Guide](../../publish.md). 