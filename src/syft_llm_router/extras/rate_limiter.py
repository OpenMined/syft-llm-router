import time
from collections import defaultdict
from functools import wraps
from threading import Lock
from typing import Callable, Optional, Union

from loguru import logger
from syft_event import Request, Response
from syft_llm_router.error import RateLimitExceededError
from typing_extensions import TypeVar

T = TypeVar("T", bound=Request)
R = TypeVar("R", bound=Response)


class RateLimiterConfig:
    """Configuration for rate limiting."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        enabled: bool = True,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.enabled = enabled


class RateLimiter:
    """Rate limiter for Syft LLM Router."""

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        """
        Initialize rate limiter with the given configuration.

        Args:
            config: Rate limiting configuration. If None, use default values.
        """
        self.config = config or RateLimiterConfig()
        self._buckets: dict[str, dict[str, dict]] = {
            "minute": defaultdict(
                lambda: {
                    "tokens": self.config.requests_per_minute,
                    "last_refill": time.time(),
                }
            ),
            "hour": defaultdict(
                lambda: {
                    "tokens": self.config.requests_per_hour,
                    "last_refill": time.time(),
                }
            ),
            "day": defaultdict(
                lambda: {
                    "tokens": self.config.requests_per_day,
                    "last_refill": time.time(),
                }
            ),
        }
        self._lock = Lock()

    def _refill_bucket(self, bucket_type: str, client_id: str) -> None:
        """Refill tokens based on time elapsed since last refill."""
        now = time.time()
        bucket = self._buckets[bucket_type][client_id]

        # Calculate time elapsed and tokens to add
        elapsed = now - bucket["last_refill"]

        if bucket_type == "minute":
            max_tokens = self.config.requests_per_minute
            refill_rate = max_tokens / 60  # tokens per second
        elif bucket_type == "hour":
            max_tokens = self.config.requests_per_hour
            refill_rate = max_tokens / 3600  # tokens per second
        else:  # day
            max_tokens = self.config.requests_per_day
            refill_rate = max_tokens / 86400  # tokens per second

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * refill_rate
        bucket["tokens"] = min(max_tokens, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = now

    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client exceeds rate limits.

        Args:
            client_id: Unique identifier for the client

        Returns:
            True if client is within rate limits, False otherwise
        """
        if not self.config.enabled:
            return True

        with self._lock:
            # Refill tokens for each bucket
            for bucket_type in self._buckets:
                self._refill_bucket(bucket_type, client_id)

            # Check if all buckets have at least one token
            has_tokens = all(
                self._buckets[bucket_type][client_id]["tokens"] >= 1
                for bucket_type in self._buckets
            )

            if has_tokens:
                # Consume tokens from all buckets
                for bucket_type in self._buckets:
                    self._buckets[bucket_type][client_id]["tokens"] -= 1
                return True

            # Log rate limit exceeded
            retry_after = self._calculate_retry_after(client_id)
            logger.warning(
                f"Rate limit exceeded for client {client_id}. "
                f"Retry after {retry_after}s"
            )
            return False

    def _calculate_retry_after(self, client_id: str) -> int:
        """Calculate seconds until rate limit resets."""
        # Find the bucket with the lowest token refill rate
        min_seconds = float("inf")

        for bucket_type, bucket_dict in self._buckets.items():
            bucket = bucket_dict[client_id]

            if bucket_type == "minute":
                refill_rate = self.config.requests_per_minute / 60
            elif bucket_type == "hour":
                refill_rate = self.config.requests_per_hour / 3600
            else:  # day
                refill_rate = self.config.requests_per_day / 86400

            # Calculate seconds until 1 token is available
            if refill_rate > 0:
                seconds_to_refill = max(0, (1 - bucket["tokens"]) / refill_rate)
                min_seconds = min(min_seconds, seconds_to_refill)

        return int(min_seconds) + 1  # Add 1 second buffer


def rate_limit(limiter: RateLimiter):
    """
    Decorator to apply rate limiting to route handlers.

    Args:
        limiter: RateLimiter instance to use

    Returns:
        Decorated function
    """

    def decorator(
        func: Callable[[T, Request], Union[R, RateLimitExceededError]],
    ):
        @wraps(func)
        def wrapper(request: T, ctx: Request) -> Union[R, RateLimitExceededError]:
            client_id = str(ctx.sender)

            if limiter.check_rate_limit(client_id):
                return func(request, ctx)

            # Return rate limit error
            retry_after = limiter._calculate_retry_after(client_id)
            return RateLimitExceededError(
                data={"retry_after": retry_after},
            )

        return wrapper

    return decorator
