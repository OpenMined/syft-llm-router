import argparse
from pathlib import Path
from typing import Optional, Union

from loguru import logger
from pydantic import BaseModel
from syft_core import Client
from syft_event import SyftEvents
from syft_event.types import Request
from syft_llm_router import BaseLLMRouter
from syft_llm_router.error import (
    EndpointNotImplementedError,
    Error,
    InvalidRequestError,
)
from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    EmbeddingOptions,
    GenerationOptions,
    Message,
    RetrievalOptions,
    RetrievalResponse,
)
from watchdog.events import FileSystemEvent


class ChatRequest(BaseModel):
    """Chat request model."""

    model: str
    messages: list[Message]
    options: Optional[GenerationOptions] = None


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

    from router import SyftRAGRouter

    return SyftRAGRouter()


def get_embedder_endpoint() -> str:
    """Get the embedder endpoint."""
    return "http://localhost:8000/embed"


def get_indexer_endpoint() -> str:
    """Get the indexer endpoint."""
    return "http://localhost:8001/index"


def get_retriever_endpoint() -> str:
    """Get the retriever endpoint."""
    return "http://localhost:8001/search"


def create_server(project_name: str, config_path: Optional[Path] = None):
    """Create and return the SyftEvents server with the given config path."""
    if config_path:
        client = Client.load(path=config_path)
    else:
        client = Client.load()

    server_name = f"llm/{project_name}"
    return SyftEvents(server_name, client=client)


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
    except EndpointNotImplementedError as e:
        logger.error(f"Error processing request: {e}")
        response = EndpointNotImplementedError(message=str(e))
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
    try:
        response = provider.generate_chat(
            model=request.model,
            messages=request.messages,
            options=request.options,
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = InvalidRequestError(message=str(e))
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
    logger.info(f"Listening for changes to {event.src_path}")
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
            watch_path=event.src_path,
            embedder_endpoint=embedder_endpoint,
            indexer_endpoint=indexer_endpoint,
            options=options,
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = InvalidRequestError(message=str(e))

    return response


def ping(ctx: Request) -> str:
    """Ping the server."""
    return "pong"


def create_embedding_directory(datasite_path: Path):
    """Create a directory for embeddings."""
    # Create the embeddings directory
    embeddings_dir = datasite_path / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created embeddings directory at {embeddings_dir}")
    return embeddings_dir


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

    # Register routes
    register_routes(box)

    # Create the embeddings directory
    create_embedding_directory(box.client.my_datasite)

    try:
        print("Starting server...")
        box.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error running server: {e}")
