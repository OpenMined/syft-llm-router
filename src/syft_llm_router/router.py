from abc import ABC, abstractmethod
from syft_llm_router.schema import (
    CompletionRequest,
    CompletionResponse,
    ChatRequest,
    ChatResponse,
)


class BaseLLMRouter(ABC):
    @abstractmethod
    def generate_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Generate a text completion based on a prompt."""
        raise NotImplementedError

    @abstractmethod
    def generate_chat(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat response based on a conversation history."""
        raise NotImplementedError
