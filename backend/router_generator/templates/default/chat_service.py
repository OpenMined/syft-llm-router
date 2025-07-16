"""Default chat service implementation using Ollama."""

import os
from typing import List, Optional
from uuid import uuid4

import requests
from loguru import logger

from base_services import ChatService
from schema import ChatResponse, GenerationOptions, Message, Usage
from config import load_config


DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaChatService(ChatService):
    """Ollama chat service implementation."""

    def __init__(self):
        """Initialize Ollama chat service."""

        config = load_config()
        self.base_url = config.get_service_url("chat") or DEFAULT_OLLAMA_URL
        logger.info(f"Initialized Ollama chat service with base URL: {self.base_url}")

    def generate_chat(
        self,
        model: str,
        messages: List[Message],
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response using Ollama."""
        try:
            # Prepare request payload
            payload = {
                "model": model,
                "messages": [msg.dict() for msg in messages],
                "stream": False,
            }

            # Add generation options if provided
            if options:
                if options.temperature is not None:
                    payload["temperature"] = options.temperature
                if options.top_p is not None:
                    payload["top_p"] = options.top_p
                if options.max_tokens is not None:
                    payload["num_predict"] = options.max_tokens
                if options.stop_sequences:
                    payload["stop"] = options.stop_sequences

            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            ollama_response = response.json()

            # Convert Ollama response to our schema
            assistant_message = Message(
                role="assistant",
                content=ollama_response["message"]["content"],
            )

            # Estimate token usage (Ollama doesn't provide exact counts)
            prompt_tokens = sum(len(msg.content.split()) for msg in messages)
            completion_tokens = len(assistant_message.content.split())
            total_tokens = prompt_tokens + completion_tokens

            usage = Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            return ChatResponse(
                id=uuid4(),
                model=model,
                message=assistant_message,
                usage=usage,
                provider_info={"provider": "ollama", "model": model},
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in chat generation: {e}")
            raise e


ChatServiceImpl = OllamaChatService
