from abc import ABC, abstractmethod
from typing import Optional

from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    EmbeddingOptions,
    EmbeddingResponse,
    GenerationOptions,
    Message,
    RetrievalOptions,
    RetrievalResponse,
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

    @abstractmethod
    def embed_documents(
        self,
        watch_path: str,
        embedder_endpoint: str,
        indexer_endpoint: str,
        options: Optional[EmbeddingOptions] = None,
    ) -> EmbeddingResponse:
        """Process JSON files in a specified location and
           create embeddings for indexing.

        Args:
            watch_path: Directory path to watch for new JSON files
            embedder_endpoint: HTTP endpoint of the embedding service
            indexer_endpoint: HTTP endpoint of the indexing service
            options: Additional parameters for embedding configuration

        Returns:
            EmbeddingResponse: The result of the document embedding operation
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_documents(
        self,
        query: str,
        embedder_endpoint: str,
        retriever_endpoint: str,
        options: Optional[RetrievalOptions] = None,
    ) -> RetrievalResponse:
        """Retrieve documents from the index based on a search query.

        Args:
            query: Search query to find relevant documents
            embedder_endpoint: HTTP endpoint of the embedding service
            retriever_endpoint: HTTP endpoint of the retriever service
            options: Additional parameters for retrieval configuration

        Returns:
            RetrievalResponse: The result of the document retrieval operation
        """
        raise NotImplementedError
