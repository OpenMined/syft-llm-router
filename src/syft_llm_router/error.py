from typing import Optional

from pydantic import BaseModel, Field


class RouterError(BaseModel):
    """Base error model for LLM router errors."""

    code: int
    message: str
    data: Optional[dict] = Field(
        None, description="Additional data related to the error"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "code": 400,
                "message": "Invalid request",
                "data": {"details": "Invalid input format"},
            }
        }


class ModelNotFoundError(RouterError):
    """Error when the requested model cannot be found."""

    code: int = 404
    message: str = Field(
        default="Model not found",
        description="Error message for model not found errors",
    )


class InvalidRequestError(RouterError):
    """Error when the request is invalid."""

    code: int = 400
    message: str = Field(
        default="Invalid request",
        description="Error message for invalid request errors",
    )


class RateLimitExceededError(RouterError):
    """Error when rate limits have been exceeded."""

    code: int = 429
    message: str = Field(
        default="Rate limit exceeded. Please try again later.",
        description="Error message for rate limit exceeded errors",
    )


class FileProcessingError(RouterError):
    """Error when a file cannot be processed."""

    code: int = 500
    message: str = Field(
        default="File processing error",
        description="Error message for file processing errors",
    )


class EmbeddingServiceError(RouterError):
    """Error when the embedding service fails."""

    code: int = 502
    message: str = Field(
        default="Embedding service error",
        description="Error message for embedding service errors",
    )


class IndexerServiceError(RouterError):
    """Error when the indexer service fails."""

    code: int = 503
    message: str = Field(
        default="Indexer service error",
        description="Error message for indexer service errors",
    )


class EndpointNotImplementedError(RouterError):
    """Error when an endpoint is not implemented."""

    code: int = 501
    message: str = Field(
        default="Endpoint not implemented",
        description="Error message for endpoint not implemented errors",
    )
