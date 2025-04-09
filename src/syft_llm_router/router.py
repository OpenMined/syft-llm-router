from abc import ABC, abstractmethod
from typing import Optional

from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    GenerationOptions,
    Message,
)


class BaseLLMRouter(ABC):
    @abstractmethod
    def generate_completion(
        self,
        model: str,
        prompt: str,
        options: Optional[GenerationOptions] = None,
    ) -> CompletionResponse:
        """Generate a text completion based on a prompt."""
        raise NotImplementedError

    @abstractmethod
    def generate_chat(
        self,
        model: str,
        messages: list[Message],
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response based on a conversation history."""
        raise NotImplementedError
