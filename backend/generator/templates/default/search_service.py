"""Default search service implementation using local ChromaDB."""

import os
from typing import Optional
from uuid import uuid4

from loguru import logger
import httpx

from base_services import SearchService
from schema import DocumentResult, SearchOptions, SearchResponse
from config import RouterConfig
from pydantic import EmailStr


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

        self._check_if_rag_is_ready()

    def _check_if_rag_is_ready(self):
        try:
            response = self.rag_client.get("/api/stats")
            response.raise_for_status()
            logger.info("RAG is ready")
        except Exception as e:
            logger.error(f"RAG is not ready: {e}")

    def search_documents(
        self,
        query: str,
        user_email: EmailStr,
        transaction_token: str,
        options: Optional[SearchOptions] = None,
    ) -> SearchResponse:
        """Search documents using local RAG."""

        limit = options.limit if options else MAX_DOCUMENT_LIMIT_PER_QUERY
        try:
            with self.accounting_client.delegated_transfer(
                user_email,
                amount=0.1,
                token=transaction_token,
            ) as payment_txn:
                response = self.rag_client.post(
                    "/api/search",
                    json={
                        "query": query,
                        "limit": limit,
                    },
                )
                response.raise_for_status()

            response_json = response.json()

            results = response_json["results"]
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

            if len(documents) > 0:
                payment_txn.confirm()

            return SearchResponse(
                id=uuid4(),
                query=query,
                results=documents,
                provider_info={"provider": "local_rag"},
            )

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            raise e


SearchServiceImpl = LocalSearchService
