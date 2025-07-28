"""Default search service implementation using local ChromaDB."""

import os
from typing import Optional
from uuid import uuid4

from loguru import logger
import httpx

from base_services import SearchService
from schema import (
    DocumentResult,
    SearchOptions,
    SearchResponse,
    PublishedMetadata,
    RouterServiceType,
)
from config import RouterConfig
from pydantic import EmailStr
from syft_accounting_sdk import UserClient


MAX_DOCUMENT_LIMIT_PER_QUERY = 10


class LocalSearchService(SearchService):
    """Local RAG service using ChromaDB and Sentence Transformers."""

    def __init__(self, config: RouterConfig):
        """Initialize local RAG service."""
        super().__init__(config)
        self.rag_url = self.config.get_service_url("search")
        if not self.rag_url:
            raise ValueError("Search service URL not found in configuration")
        logger.info(f"Initialized local RAG service with URL: {self.rag_url}")

        self.rag_client = httpx.Client(base_url=self.rag_url)
        self.accounting_client: UserClient = self.config.accounting_client()
        logger.info(f"Initialized accounting client: {self.accounting_client}")

        self._check_if_rag_is_ready()

    def _check_if_rag_is_ready(self):
        """Check if RAG is ready."""
        try:
            response = self.rag_client.get("/api/stats")
            response.raise_for_status()
            logger.info("RAG is ready")
        except Exception as e:
            logger.error(f"RAG is not ready: {e}")

    def __make_search_request(self, payload: dict) -> list[dict]:
        """Make a search request to the RAG service."""
        response = self.rag_client.post(
            "/api/search",
            json=payload,
        )
        response.raise_for_status()

        response_json = response.json()

        return response_json["results"]

    def search_documents(
        self,
        user_email: EmailStr,
        query: str,
        transaction_token: Optional[str] = None,
        options: Optional[SearchOptions] = None,
    ) -> SearchResponse:
        """Search documents using local RAG."""

        limit = options.limit if options else MAX_DOCUMENT_LIMIT_PER_QUERY

        query_cost = 0.0

        try:

            if self.pricing > 0 and transaction_token:
                # If pricing is not zero, then we need to create a transaction
                with self.accounting_client.delegated_transfer(
                    user_email,
                    amount=self.pricing,
                    token=transaction_token,
                ) as payment_txn:
                    results = self.__make_search_request(query, limit)

                    if len(results) > 0:
                        payment_txn.confirm()
                    query_cost = self.pricing
            elif self.pricing > 0 and not transaction_token:
                # If pricing is not zero, but transaction token is not provided, then we raise an error
                raise ValueError(
                    "Transaction token is required for paid services. Please provide a transaction token."
                )
            else:
                # If pricing is zero, then we make a request to RAG without creating a transaction
                # We don't need to create a transaction because the service is free
                results = self.__make_search_request(query, limit)

            documents = [
                DocumentResult(
                    id=str(result["id"]),
                    score=result["similarity"],
                    content=result["content"],
                    metadata={
                        "filename": result["filename"],
                    },
                    provider_info={
                        "provider": "local_rag",
                        "results_count": len(results),
                    },
                )
                for result in results
            ]

            return SearchResponse(
                id=uuid4(),
                query=query,
                results=documents,
                provider_info={"provider": "local_rag"},
                cost=query_cost,
            )

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            raise e

    @property
    def pricing(self) -> float:
        """Get the pricing for the search service."""
        if not self.config.metadata_path.exists():
            return 0.0
        metadata = PublishedMetadata.from_path(self.config.metadata_path)
        for service in metadata.services:
            if service.type == RouterServiceType.SEARCH:
                return service.pricing


SearchServiceImpl = LocalSearchService
