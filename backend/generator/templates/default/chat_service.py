"""Default chat service implementation using Ollama."""

import os
from typing import List, Optional
from uuid import uuid4

import requests
from loguru import logger

from base_services import ChatService
from schema import (
    ChatResponse,
    GenerationOptions,
    Message,
    ChatUsage,
    PublishedMetadata,
    RouterServiceType,
)
from config import RouterConfig
from pydantic import EmailStr
from syft_accounting_sdk import UserClient


DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaChatService(ChatService):
    """Ollama chat service implementation."""

    def __init__(self, config: RouterConfig):
        """Initialize Ollama chat service."""

        super().__init__(config)
        self.base_url = self.config.get_service_url("chat") or DEFAULT_OLLAMA_URL
        logger.info(f"Initialized Ollama chat service with base URL: {self.base_url}")

        self.accounting_client: UserClient = self.config.accounting_client()
        logger.info(f"Initialized accounting client: {self.accounting_client}")

    def __make_chat_request(self, payload: dict) -> dict:
        """Make a search request to the Ollama API."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        ollama_response = response.json()

        content = ollama_response["message"]["content"]

        return content

    def generate_chat(
        self,
        model: str,
        messages: List[Message],
        user_email: EmailStr,
        transaction_token: Optional[str] = None,
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

            # Initialize query cost to 0.0
            query_cost = 0.0

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

            if self.pricing > 0 and transaction_token:
                # If pricing is not zero, then we need to create a transaction
                with self.accounting_client.delegated_transfer(
                    user_email,
                    amount=self.pricing,
                    token=transaction_token,
                ) as payment_txn:
                    # Make request to Ollama
                    content = self.__make_chat_request(payload)

                    # If the response is not empty, confirm the transaction
                    if content:
                        payment_txn.confirm()

                    query_cost = self.pricing

            elif self.pricing > 0 and not transaction_token:
                # If pricing is not zero, but transaction token is not provided, then we raise an error
                raise ValueError(
                    "Transaction token is required for paid services. Please provide a transaction token."
                )

            else:
                # If pricing is zero, then we make a request to Ollama without creating a transaction
                # We don't need to create a transaction because the service is free
                # Make request to Ollama
                content = self.__make_chat_request(payload)

            # Convert Ollama response to our schema
            assistant_message = Message(
                role="assistant",
                content=content,
            )

            # Estimate token usage (Ollama doesn't provide exact counts)
            prompt_tokens = sum(len(msg.content.split()) for msg in messages)
            completion_tokens = len(assistant_message.content.split())
            total_tokens = prompt_tokens + completion_tokens

            usage = ChatUsage(
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
                cost=query_cost,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in chat generation: {e}")
            raise e

    @property
    def pricing(self) -> float:
        """Get the pricing for the chat service."""
        if not self.config.metadata_path.exists():
            return 0.0
        metadata = PublishedMetadata.from_path(self.config.metadata_path)
        for service in metadata.services:
            if service.type == RouterServiceType.CHAT:
                return service.pricing


ChatServiceImpl = OllamaChatService
