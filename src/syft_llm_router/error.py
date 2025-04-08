from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import TypeVar


class BaseError(BaseModel):
    """Base error model for LLM router errors."""

    code: int
    message: str
    data: Optional[dict] = Field(
        None, description="Additional data related to the error"
    )

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "code": 400,
                "message": "Invalid request",
                "data": {"details": "Invalid input format"},
            }
        }


class ModelNotFoundError(BaseError):
    """Error when the requested model cannot be found."""

    code: int = 404
    message: str = Field(
        default="Model not found",
        description="Error message for model not found errors",
    )


class InvalidRequestError(BaseError):
    """Error when the request is invalid."""

    code: int = 400
    message: str = Field(
        default="Invalid request",
        description="Error message for invalid request errors",
    )


class RateLimitExceededError(BaseError):
    """Error when rate limits have been exceeded."""

    code: int = 429
    message: str = Field(
        default="Rate limit exceeded",
        description="Error message for rate limit exceeded errors",
    )


RouterError = TypeVar("RouterError", bound=BaseError, covariant=True)
