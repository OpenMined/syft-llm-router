# Syft LLM Router RAG App Example

This example demonstrates how to build a Retrieval-Augmented Generation (RAG) application using the Syft LLM Router. The app provides a server implementation that handles chat completions, document embeddings, and document retrieval.

## Features

- **Chat Completions**: Generate responses using LLM models with context from retrieved documents
- **Document Embedding**: Convert documents into vector embeddings for semantic search
- **Document Retrieval**: Search and retrieve relevant documents based on user queries
- **File System Monitoring**: Automatically process new documents added to a watched directory
- **Rate Limiting**: Configurable rate limiting for API endpoints
- **Error Handling**: Comprehensive error handling and logging

## Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Access to LLM models (configured through environment variables)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/OpenMined/syft-llm-router.git
cd syft-llm-router/examples/rag-app
```

2. Create and activate the virtual environment:
```bash
uv venv -p 3.12 .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
uv pip install .
```

## Configuration

The app can be configured through the `pyproject.toml` file:

```toml
[tool.rag-app]
# Rate limiting settings
enable_rate_limiting = true
requests_per_minute = 1
requests_per_hour = 10
requests_per_day = 1000

# Embedding settings
embedder_endpoint = ""
indexer_endpoint = ""

# Retrieval settings
retriever_endpoint = ""
```

## Usage

1. Start the server:
```bash
./run.sh
```

The server will:
- Create necessary directories for embeddings
- Start listening for incoming requests
- Monitor specified directories for new documents
- Automatically process and index new documents

## API Endpoints

### Chat Completion
- **Endpoint**: `/chat`
- **Method**: POST
- **Request Body**:
```json
{
    "model": "string",
    "messages": [
        {
            "role": "string",
            "content": "string"
        }
    ],
    "options": {
        "temperature": 0.7,
        "max_tokens": 1000
    }
}
```

### Document Retrieval
- **Endpoint**: `/retrieve`
- **Method**: POST
- **Request Body**:
```json
{
    "query": "string",
    "options": {
        "top_k": 5
    }
}
```

### Document Embedding
- **Endpoint**: `/embed`
- **Method**: POST
- Automatically triggered when new documents are added to the watched directory

## Architecture

The app consists of three main components:

1. **Router (`router.py`)**: Implements the core RAG functionality:
   - Document processing and chunking
   - Embedding generation
   - Document retrieval
   - Chat completion with context

2. **Server (`server.py`)**: Handles HTTP requests and routes them to the appropriate handlers:
   - Request validation
   - Error handling
   - Rate limiting
   - File system monitoring

3. **Configuration (`pyproject.toml`)**: Manages app settings:
   - Rate limiting parameters
   - API endpoints
   - Dependencies

## Error Handling

The app includes comprehensive error handling for:
- Invalid requests
- Unimplemented endpoints
- Processing errors
- Rate limiting violations

All errors are logged using the `loguru` library for easy debugging.

## License

This example is part of the Syft LLM Router project and is licensed under the same terms as the main project.
