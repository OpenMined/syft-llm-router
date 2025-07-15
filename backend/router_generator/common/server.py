#!/usr/bin/env python3
"""FastAPI server for Syft LLM Router with factory pattern for service loading."""

import argparse
import random
import socket
import os
import json
from typing import List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastsyftbox import FastSyftBox
from fastapi import HTTPException
from fastapi.openapi.utils import get_openapi
from loguru import logger
from pydantic import BaseModel
from syft_core.config import SyftClientConfig
from pathlib import Path

from config import load_config, RunStatus
from router import SyftLLMRouter
from schema import (
    ChatResponse,
    GenerateChatParams,
    SearchOptions,
    SearchResponse,
)


def generate_openapi_schema(app: FastSyftBox):
    """Generate OpenAPI schema for the FastSyftBox application."""

    app_name = app.app_name
    with open(f"{app_name}.openapi.json", "w") as f:
        f.write(
            json.dumps(
                get_openapi(
                    title=app_name,
                    version="1.0.0",
                    routes=app._get_api_routes_with_tags(tags=["syftbox"]),
                    description="This is a SyftBox application with RPC endpoints.",
                ),
                indent=2,
            )
        )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    project_name: str
    services: dict


@asynccontextmanager
async def lifespan(app: FastSyftBox):
    """Custom lifespan method to initialize router and handle startup/shutdown."""
    try:
        # Startup logic
        config = load_config()
        global router
        router = SyftLLMRouter()
        logger.info(f"Router initialized for project: {config.project_name}")
        generate_openapi_schema(app)

        app_port = os.environ.get("APP_PORT", 8000)
        app_host = os.environ.get("APP_HOST", "0.0.0.0")

        config.state.update_router_state(
            status=RunStatus.RUNNING,
            url=f"http://{app_host}:{app_port}",
        )

        yield  # This allows the application to run

    except Exception as e:
        logger.error(f"Failed to initialize router: {e}")
        raise

    finally:
        # Optional cleanup logic if needed
        # For example, closing any resources
        logger.info("Application shutting down")
        config.state.update_router_state(status=RunStatus.STOPPED)


app_name = Path(__file__).resolve().parent.name

# Create FastAPI app
app = FastSyftBox(
    app_name=app_name,
    description="A router for LLM services with consistent API",
    version="1.0.0",
    syftbox_endpoint_tags=["syftbox"],
    include_syft_openapi=True,
    lifespan=lifespan,
    syftbox_config=SyftClientConfig.load(
        "/home/shubham/.syftbox/config.alice.dev.json"
    ),
)

# Global router instance
router: Optional[SyftLLMRouter] = None


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["syftbox"],
    summary="Health check",
    description="Health check",
)
async def health_check():
    """Health check endpoint.

    Returns:
        HealthResponse: The health check response from the router
    """
    if not router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    config = load_config()

    # Check service availability
    services = config.state.services.model_dump()

    return HealthResponse(
        status="healthy",
        project_name=config.project_name,
        services=services,
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["syftbox"],
    summary="Chat with the router",
    description="Chat with the router",
    responses={200: {"model": ChatResponse}},
)
async def chat_completion(request: GenerateChatParams):
    """Chat completion endpoint.

    Args:
        request (GenerateChatParams): The request body containing the chat completion parameters

    Returns:
        ChatResponse: The chat completion response from the router
    """
    if not router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    try:
        return router.generate_chat(request.model, request.messages, request.options)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail="Chat completion failed")


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["syftbox"],
    summary="Search documents",
    description="Search documents",
    responses={200: {"model": SearchResponse}},
)
async def search_documents(
    query: str,
    options: Optional[SearchOptions] = None,
):
    """Document retrieval endpoint.

    Args:
        query (str): The search query
        options (Optional[SearchOptions]): The search options

    Returns:
        SearchResponse: The search response from the router
    """
    if not router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    try:
        return router.search_documents(query, options)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Document retrieval failed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Syft LLM Router Server")
    parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (overrides PROJECT_NAME env var)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    # Set project name if provided
    if args.project_name:
        os.environ["PROJECT_NAME"] = args.project_name

    # Configure logging
    logger.add(
        "router.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
    )

    app.app_name = os.environ["PROJECT_NAME"]

    logger.info("Starting Syft LLM Router server...")

    # Check if port is already in use
    if is_port_in_use(args.port):
        # Choose a random port
        args.port = random.randint(10000, 65535)
        logger.warning(
            f"Port {args.port} is already in use. Using random port: {args.port}"
        )

    os.environ["APP_PORT"] = str(args.port)
    os.environ["APP_HOST"] = args.host

    # Start server
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
