"""Custom chat service implementation template.

Implement your own chat service logic here.
"""

from typing import List, Optional
from uuid import UUID

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
from pydantic import EmailStr
from config import RouterConfig
from syft_accounting_sdk import UserClient


class CustomChatService(ChatService):
    """Custom chat service implementation.

    TODO: Implement your chat service logic here.
    """

    def __init__(self, config: RouterConfig):
        """Initialize custom chat service."""
        super().__init__(config)
        # TODO: Add your initialization logic here
        # Example: API keys, base URLs, model configurations, etc.
        self.accounting_client: UserClient = self.config.accounting_client()
        logger.info(f"Initialized accounting client: {self.accounting_client}")
        logger.info("Initialized custom chat service")

    def generate_chat(
        self,
        model: str,
        messages: List[Message],
        user_email: EmailStr,
        transaction_token: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response using your custom implementation."""
        # TODO: Implement your chat generation logic here
        # Example implementation:

        # 1. Prepare the request payload for your chat service
        # payload = {
        #     "model": model,
        #     "messages": [msg.dict() for msg in messages],
        #     "stream": False,
        # }
        # if options:
        #     if options.temperature is not None:
        #         payload["temperature"] = options.temperature
        #     if options.top_p is not None:
        #         payload["top_p"] = options.top_p
        #     if options.max_tokens is not None:
        #         payload["num_predict"] = options.max_tokens
        #     if options.stop_sequences:
        #         payload["stop"] = options.stop_sequences

        # 2. Handle payment transaction if pricing > 0
        # query_cost = 0.0
        # if self.pricing > 0 and transaction_token:
        #     with self.accounting_client.delegated_transfer(
        #         user_email,
        #         amount=self.pricing,
        #         token=transaction_token,
        #     ) as payment_txn:
        #         # Make request to your chat service
        #         response = requests.post("your_api_endpoint", json=payload)
        #         response.raise_for_status()
        #         response_data = response.json()
        #         # Confirm transaction if response is valid
        #         if response_data:
        #             payment_txn.confirm()
        #         query_cost = self.pricing
        # elif self.pricing > 0 and not transaction_token:
        #     raise ValueError(
        #         "Transaction token is required for paid services. Please provide a transaction token."
        #     )
        # else:
        #     # Free service, just make the request
        #     response = requests.post("your_api_endpoint", json=payload)
        #     response.raise_for_status()
        #     response_data = response.json()

        # 3. Convert the response to our schema format
        # assistant_message = Message(
        #     role="assistant",
        #     content=response_data["content"],
        # )

        # 4. Estimate or extract token usage
        # prompt_tokens = sum(len(msg.content.split()) for msg in messages)
        # completion_tokens = len(assistant_message.content.split())
        # total_tokens = prompt_tokens + completion_tokens
        # usage = ChatUsage(
        #     prompt_tokens=prompt_tokens,
        #     completion_tokens=completion_tokens,
        #     total_tokens=total_tokens,
        # )

        # 5. Return ChatResponse
        # return ChatResponse(
        #     id=UUID.uuid4(),
        #     model=model,
        #     message=assistant_message,
        #     usage=usage,
        #     provider_info={"provider": "custom", "response": response_data},
        #     cost=query_cost,
        # )

        # Placeholder implementation (remove this when implementing)
        raise NotImplementedError(
            "Custom chat service not implemented. "
            "Please implement the generate_chat method in chat_service.py"
        )

    @property
    def pricing(self) -> float:
        """Get the pricing for the chat service."""
        if not self.config.metadata_path.exists():
            return 0.0
        metadata = PublishedMetadata.from_path(self.config.metadata_path)
        for service in metadata.services:
            if service.type == RouterServiceType.CHAT:
                return service.pricing


ChatServiceImpl = CustomChatService
