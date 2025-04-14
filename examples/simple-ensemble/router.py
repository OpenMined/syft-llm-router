from typing import Optional

from syft_llm_router import BaseLLMRouter
from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    GenerationOptions,
    Message,
)


class SyftLLMRouter(BaseLLMRouter):
    """Syft LLM Router class.

    This class is a placeholder for the actual implementation of the Syft LLM provider.
    It should be extended to implement the specific functionality required by your application.
    """

    raise NotImplementedError(
        "The BaseLLMRouter class is a placeholder. "
        "Please implement the required functionality in your subclass."
    )

    def generate_completion(
        self,
        model: str,
        prompt: str,
        options: Optional[GenerationOptions] = None,
    ) -> CompletionResponse:
        """Generate a text completion based on a prompt."""
        raise NotImplementedError

    def generate_chat(
        self,
        model: str,
        messages: list[Message],
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response based on a conversation history."""
        raise NotImplementedError
