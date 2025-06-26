import argparse
import os
import accounting
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Union
import tomllib

from watchdog.events import FileSystemEvent
from loguru import logger
from syft_core import Client
from syft_event import SyftEvents
from syft_event.types import Request
from syft_llm_router import BaseLLMRouter
from syft_llm_router.error import (
    EmbeddingServiceError,
    IndexerServiceError,
    InvalidRequestError,
    FileProcessingError,
    Error,
)
from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    GenerationOptions,
    Message,
    RetrievalOptions,
    RetrievalResponse,
    EmbeddingOptions,
)


class ChatRequest(BaseModel):
    """Chat request model."""

    model: str
    messages: list[Message]
    options: Optional[GenerationOptions] = None
    accounting_token: str


class DocumentRetrievalRequest(BaseModel):
    """Document retrieval request model."""

    query: str
    options: Optional[RetrievalOptions] = None


class CompletionRequest(BaseModel):
    """Completion request model."""

    model: str
    prompt: str
    options: Optional[GenerationOptions] = None


def load_router() -> BaseLLMRouter:
    """Load your implementation of the LLM provider."""

    # This is a placeholder for the actual provider loading logic.
    # You should replace this with the actual provider you want to use.
    # For example, if you have a provider class named `MyLLMProvider`, you would do:
    # from my_llm_provider import MyLLMProvider
    # args = ...  # Load or define your provider arguments here
    # kwargs = ...  # Load or define your provider keyword arguments here
    # provider = MyLLMProvider(*args, **kwargs)
    # return provider
    from router import SyftLLMRouter

    return SyftLLMRouter()


def get_embedder_endpoint() -> str:
    """Get the embedder endpoint."""
    return os.getenv("EMBEDDER_ENDPOINT", "http://localhost:8000/embedder")


def get_indexer_endpoint() -> str:
    """Get the indexer endpoint."""
    return os.getenv("INDEXER_ENDPOINT", "http://localhost:8000/indexer")


def get_retriever_endpoint() -> str:
    """Get the retriever endpoint."""
    return os.getenv("RETRIEVER_ENDPOINT", "http://localhost:8000/retriever")


def create_server(project_name: str, config_path: Optional[Path] = None):
    """Create and return the SyftEvents server with the given config path."""
    if config_path:
        client = Client.load(path=config_path)
    else:
        client = Client.load()

    server_name = f"routers/{project_name}"
    return SyftEvents(server_name, client=client)


def get_pricing_per_request() -> float:
    """Get the pricing per request from pyproject.toml."""
    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        return config.get("tool", {}).get("my-llm-router", {}).get("pricing_per_request", 0.1)
    except Exception as e:
        logger.warning(f"Could not read pricing_per_request from pyproject.toml: {e}. Using default value 0.1")
        return 0.1


def handle_completion_request(
    request: CompletionRequest,
    ctx: Request,
) -> Union[CompletionResponse, Error]:
    """Handle a completion request."""

    logger.info(f"Processing completion request: <{ctx.id}>from <{ctx.sender}>")
    provider = load_router()

    try:
        response = provider.generate_completion(
            model=request.model,
            prompt=request.prompt,
            options=request.options,
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = InvalidRequestError(message=str(e))
    return response


def handle_chat_completion_request(
    request: ChatRequest,
    ctx: Request,
) -> Union[ChatResponse, Error]:
    """Handle a chat completion request."""
    logger.info(f"Processing chat request: <{ctx.id}>from <{ctx.sender}>")
    provider = load_router()
    accounting_client = accounting.get_or_init_user_client()

    try:
        transaction = accounting_client.create_delegated_transaction(
            amount=get_pricing_per_request(), senderEmail=ctx.sender, token=request.accounting_token
        )
    except Exception as e:
        return InvalidRequestError(message=str(e))

    try:
        response = provider.generate_chat(
            model=request.model,
            messages=request.messages,
            options=request.options,
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        accounting_client.cancel_transaction(id=transaction.id)
        response = InvalidRequestError(message=str(e))

    accounting_client.confirm_transaction(id=transaction.id)
    return response


def handle_document_retrieval_request(
    request: DocumentRetrievalRequest,
    ctx: Request,
) -> Union[RetrievalResponse, Error]:
    """Handle a document retrieval request."""
    logger.info(f"Processing document retrieval request: <{ctx.id}>from <{ctx.sender}>")
    provider = load_router()
    embedder_endpoint = get_embedder_endpoint()
    retriever_endpoint = get_retriever_endpoint()
    try:
        response = provider.retrieve_documents(
            query=request.query,
            options=request.options,
            embedder_endpoint=embedder_endpoint,
            retriever_endpoint=retriever_endpoint,
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = InvalidRequestError(message=str(e))
    return response


def handle_document_embeddings(event: FileSystemEvent) -> Optional[Error]:
    """Handle a document embeddings request."""
    logger.info(
        f"Processing document embeddings request: <{event.id}>from <{event.sender}>"
    )
    provider = load_router()
    embedder_endpoint = get_embedder_endpoint()
    indexer_endpoint = get_indexer_endpoint()

    options = EmbeddingOptions(
        chunk_size=1024,
        chunk_overlap=2048,
        batch_size=10,
        process_interval=10,
    )

    try:
        response = provider.embed_documents(
            watch_path=Path(event.src_path),
            embedder_endpoint=embedder_endpoint,
            indexer_endpoint=indexer_endpoint,
            options=options,
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = InvalidRequestError(message=str(e))

    return response


def create_embedding_directory(datasite_path: Path):
    """Create a directory for embeddings."""
    # Create the embeddings directory
    embeddings_dir = datasite_path / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created embeddings directory at {embeddings_dir}")
    return embeddings_dir


def ping(ctx: Request) -> str:
    """Ping the server."""
    return "pong"


def register_routes(server):
    """Register all routes on the given server instance."""
    server.on_request("/completions")(handle_completion_request)
    server.on_request("/chat")(handle_chat_completion_request)
    server.on_request("/retrieve")(handle_document_retrieval_request)
    server.watch("{datasite}/embeddings/**/*.json")(handle_document_embeddings)
    server.on_request("/ping")(ping)

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Syft LLM Router server")

    parser.add_argument(
        "--project-name",
        type=str,
        help="Name of the project instance.",
        required=True,
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to client configuration file",
        required=False,
    )

    args = parser.parse_args()

    # Create server with config path
    box = create_server(project_name=args.project_name, config_path=args.config)

    accounting.get_or_init_user_client()

    # Create the embeddings directory
    create_embedding_directory(box.client.my_datasite)

    # Register routes
    register_routes(box)

    try:
        print("Starting server...")
        box.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error running server: {e}")
