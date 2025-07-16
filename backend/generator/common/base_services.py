"""Base service interfaces for the router."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from schema import (
    ChatResponse,
    GenerationOptions,
    Message,
    SearchOptions,
    SearchResponse,
)


class ChatService(ABC):
    """Abstract interface for chat services."""

    @abstractmethod
    def generate_chat(
        self,
        model: str,
        messages: List[Message],
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response based on conversation history."""
        pass


class SearchService(ABC):
    """Abstract interface for document retrieval services."""

    @abstractmethod
    def search_documents(
        self,
        query: str,
        options: Optional[SearchOptions] = None,
    ) -> SearchResponse:
        """Search documents based on a search query."""
        pass
