"""Default search service implementation using local ChromaDB."""

import os
from typing import Optional
from uuid import uuid4

from loguru import logger
import httpx

from base_services import SearchService
from schema import DocumentResult, SearchOptions, SearchResponse
from config import load_config


MAX_DOCUMENT_LIMIT_PER_QUERY = 10


class LocalSearchService(SearchService):
    """Local RAG service using ChromaDB and Sentence Transformers."""

    def __init__(self):
        """Initialize local RAG service."""
        config = load_config()
        self.rag_url = config.rag_url
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
            raise RuntimeError("RAG is not ready")

    def search_documents(
        self,
        query: str,
        options: Optional[SearchOptions] = None,
    ) -> SearchResponse:
        """Search documents using local RAG."""

        limit = options.limit if options else MAX_DOCUMENT_LIMIT_PER_QUERY
        try:
            response = self.rag_client.post(
                "/api/search",
                json={
                    "query": query,
                    "limit": limit,
                },
            )

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

            response.raise_for_status()
            return SearchResponse(
                id=uuid4(),
                query=query,
                results=documents,
                provider_info={"provider": "local_rag", "db_path": self.db_path},
            )

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            raise RuntimeError(f"Failed to search documents for query: {query}")


SearchServiceImpl = LocalSearchService
