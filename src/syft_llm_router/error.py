from typing import Optional, TypeVar

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


Error = TypeVar("Error", bound=RouterError, covariant=True)
