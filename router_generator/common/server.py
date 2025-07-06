#!/usr/bin/env python3
"""FastAPI server for Syft LLM Router with factory pattern for service loading."""

import argparse
import os
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from config import load_config
from router import SyftLLMRouter
from schema import (
    ChatResponse,
    GenerationOptions,
    Message,
    RetrievalOptions,
    RetrievalResponse,
)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    project_name: str
    services: dict


# Create FastAPI app
app = FastAPI(
    title="Syft LLM Router",
    description="A router for LLM services with consistent API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global router instance
router: Optional[SyftLLMRouter] = None


@app.on_event("startup")
async def startup_event():
    """Initialize router on startup."""
    global router
    try:
        config = load_config()
        router = SyftLLMRouter()
        logger.info(f"Router initialized for project: {config.project_name}")
    except Exception as e:
        logger.error(f"Failed to initialize router: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    config = load_config()

    # Check service availability
    services = {
        "chat": router.chat_service is not None,
        "retrieve": router.retrieve_service is not None,
    }

    return HealthResponse(
        status="healthy",
        project_name=config.project_name,
        services=services,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_completion(
    model: str,
    messages: List[Message],
    options: Optional[GenerationOptions] = None,
):
    """Chat completion endpoint."""
    if not router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    try:
        return router.generate_chat(model, messages, options)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail="Chat completion failed")


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(
    query: str,
    options: Optional[RetrievalOptions] = None,
):
    """Document retrieval endpoint."""
    if not router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    try:
        return router.retrieve_documents(query, options)
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

    logger.info("Starting Syft LLM Router server...")

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
