"""Default retrieve service implementation using local ChromaDB."""

import json
import os
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from loguru import logger

from base_services import RetrieveService
from schema import DocumentResult, RetrievalOptions, RetrievalResponse

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "ChromaDB and Sentence Transformers not installed. "
        "Run: pip install chromadb sentence-transformers"
    )


class LocalRAGService(RetrieveService):
    """Local RAG service using ChromaDB and Sentence Transformers."""

    def __init__(self):
        """Initialize local RAG service."""
        self.db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.db_path, settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents", metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"Initialized local RAG service with DB path: {self.db_path}")

    def retrieve_documents(
        self,
        query: str,
        options: Optional[RetrievalOptions] = None,
    ) -> RetrievalResponse:
        """Retrieve documents using local RAG."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]

            # Set search parameters
            limit = options.limit if options and options.limit else 5
            n_results = min(limit, 100)  # ChromaDB limit

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            # Convert results to DocumentResult format
            documents = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                # Convert distance to similarity score (1 - distance for cosine)
                similarity_score = 1 - distance

                # Apply similarity threshold if specified
                if options and options.similarity_threshold:
                    if similarity_score < options.similarity_threshold:
                        continue

                documents.append(
                    DocumentResult(
                        id=str(i),
                        score=similarity_score,
                        content=doc,
                        metadata=metadata,
                    )
                )

            return RetrievalResponse(
                id=UUID.uuid4(),
                query=query,
                results=documents,
                provider_info={"provider": "local_rag", "db_path": self.db_path},
            )

        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            raise RuntimeError(f"Failed to retrieve documents: {e}")

    def add_documents(self, documents: List[dict]) -> None:
        """Add documents to the local index."""
        try:
            # Prepare documents for ChromaDB
            ids = []
            texts = []
            metadatas = []

            for i, doc in enumerate(documents):
                ids.append(str(i))
                texts.append(doc.get("content", ""))
                metadatas.append(doc.get("metadata", {}))

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            )

            logger.info(f"Added {len(documents)} documents to local index")

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise RuntimeError(f"Failed to add documents: {e}")
