"""Base service interfaces for the router."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr

from schema import (
    ChatResponse,
    GenerationOptions,
    Message,
    SearchOptions,
    SearchResponse,
)
from config import RouterConfig


class ChatService(ABC):
    """Abstract interface for chat services."""

    def __init__(self, config: RouterConfig):
        self.config = config

    @abstractmethod
    def generate_chat(
        self,
        model: str,
        messages: List[Message],
        user_email: EmailStr,
        transaction_token: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response based on conversation history."""
        pass


class SearchService(ABC):
    """Abstract interface for document retrieval services."""

    def __init__(self, config: RouterConfig):
        self.config = config

    @abstractmethod
    def search_documents(
        self,
        user_email: EmailStr,
        query: str,
        options: Optional[SearchOptions] = None,
        transaction_token: Optional[str] = None,
    ) -> SearchResponse:
        """Search documents based on a search query."""
        pass
