import argparse
import os
from pathlib import Path
from typing import Optional, Union

from loguru import logger
from pydantic import BaseModel
from syft_core import Client
from syft_event import SyftEvents
from syft_event.types import Request
from syft_llm_router import BaseLLMRouter
from syft_llm_router.error import Error, InvalidRequestError
from syft_llm_router.extras.rate_limiter import (
    RateLimiter,
    RateLimiterConfig,
    rate_limit,
)
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


class CompletionRequest(BaseModel):
    """Completion request model."""

    model: str
    prompt: str
    options: Optional[GenerationOptions] = None


rate_limiter_config = RateLimiterConfig(
    requests_per_minute=1,
    requests_per_hour=3,
    requests_per_day=10,
    enabled=True,
)

rate_limiter = RateLimiter(config=rate_limiter_config)


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

    from router import SyftOpenAIRouter

    api_key = os.environ.get("OPENAI_API_KEY", None)

    router = SyftOpenAIRouter(api_key=api_key)

    return router


def create_server(server_name: str, config_path: Optional[Path] = None):
    """Create and return the SyftEvents server with the given config path."""
    if config_path:
        client = Client.load(path=config_path)
    else:
        client = Client.load()
    return SyftEvents(server_name, client=client)


@rate_limit(rate_limiter)
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


@rate_limit(rate_limiter)
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


def register_routes(server):
    """Register all routes on the given server instance."""
    server.on_request("/completions")(handle_completion_request)
    server.on_request("/chat")(handle_chat_completion_request)
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Syft LLM Router server")

    parser.add_argument(
        "--server-name",
        type=str,
        default="llm",
        help="Name of the server instance. Default is 'llm'.",
        required=False,
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to client configuration file",
        required=False,
    )

    # Customization added to input OpenAI API key
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key. If not provided, will use OPENAI_API_KEY environment variable.",
    )

    args = parser.parse_args()

    # Create server with config
    box = create_server(server_name=args.server_name, config_path=args.config)

    # Register routes
    register_routes(box)

    # Set environment variables for OpenAI API key
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    try:
        print("Starting server...")
        box.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error running server: {e}")
