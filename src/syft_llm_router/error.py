from typing import Optional
from pydantic import BaseModel, Field


# Error data models
class ModelNotFoundErrorData(BaseModel):
    """Data for model not found errors."""

    model: Optional[str] = Field(None, description="The requested model ID")


class InvalidRequestErrorData(BaseModel):
    """Data for invalid request errors."""

    details: Optional[str] = Field(
        None, description="Details about the validation error"
    )


class RateLimitExceededErrorData(BaseModel):
    """Data for rate limit exceeded errors."""

    retry_after: Optional[int] = Field(
        None, description="Seconds to wait before retrying"
    )


class ModelNotFoundError(BaseModel):
    """Error when the requested model cannot be found."""

    code: int = 404  # Changed from -32001 to standard HTTP status code
    message: str = "Model not found"
    data: Optional[ModelNotFoundErrorData] = None


class InvalidRequestError(BaseModel):
    """Error when the request is invalid."""

    code: int = 400  # Changed from -32002 to standard HTTP status code
    message: str = "Invalid request"
    data: Optional[InvalidRequestErrorData] = None


class RateLimitExceededError(BaseModel):
    """Error when rate limits have been exceeded."""

    code: int = 429  # Changed from -32003 to standard HTTP status code
    message: str = "Rate limit exceeded"
    data: Optional[RateLimitExceededErrorData] = None
