import argparse
import os
import accounting
import tomllib
from pathlib import Path
from typing import Optional, Union

from loguru import logger
from pydantic import BaseModel
from syft_core import Client
from syft_event import SyftEvents
from syft_event.types import Request
from syft_llm_router import BaseLLMRouter
from syft_llm_router.error import Error, InvalidRequestError
from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    GenerationOptions,
    Message,
)


class ChatRequest(BaseModel):
    """Chat request model."""

    model: str
    messages: list[Message]
    options: Optional[GenerationOptions] = None
    accounting_token: str


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
    from router import DeepSeekLLMRouter

    router = DeepSeekLLMRouter(api_key=os.getenv("DEEPSEEK_API_KEY"))
    return router


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
        return config.get("tool", {}).get("deepseek", {}).get("pricing_per_request", 0.1)
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


def ping(ctx: Request) -> str:
    """Ping the server."""
    return "pong"


def register_routes(server):
    """Register all routes on the given server instance."""
    server.on_request("/completions")(handle_completion_request)
    server.on_request("/chat")(handle_chat_completion_request)
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
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API key",
        required=True,
    )

    args = parser.parse_args()

    # Create server with config
    box = create_server(project_name=args.project_name, config_path=args.config)

    # Initialize accounting client
    accounting.get_or_init_user_client()

    # Register routes
    register_routes(box)

    # Set the API key
    if args.api_key:
        os.environ["DEEPSEEK_API_KEY"] = args.api_key

    try:
        print("Starting server...")
        box.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error running server: {e}") 