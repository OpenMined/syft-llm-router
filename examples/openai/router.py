import uuid
from typing import Optional

from syft_llm_router import BaseLLMRouter
from syft_llm_router.schema import (
    ChatResponse,
    CompletionResponse,
    FinishReason,
    GenerationOptions,
    LogProbs,
    Message,
    Role,
    Usage,
)

try:
    from openai import OpenAI

    HAS_OPENAI = True

except ImportError:
    HAS_OPENAI = False


def clean_extensions(extensions: dict, prefix: str) -> dict:
    """Clean extension keys by removing the prefix and adding valid extensions to options.

    Args:
        extensions: Dictionary of extension options
        prefix: Prefix to remove from keys (e.g., "x-openai-")

    Returns:
        Dictionary with cleaned keys for valid extensions
    """
    cleaned = {}
    for key, value in extensions.items():
        if key.startswith(prefix):
            clean_key = key[len(prefix) :]  # Remove prefix
            cleaned[clean_key] = value
    return cleaned


class SyftOpenAIRouter(BaseLLMRouter):
    """OpenAI provider implementation for the SyftBox LLM Specification."""

    def __init__(
        self, api_key: Optional[str] = None, organization: Optional[str] = None
    ):
        """Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key. If None, will try to use OPENAI_API_KEY env variable.
            organization: OpenAI organization ID. If None, will try to use OPENAI_ORG_ID env variable.
        """
        if not HAS_OPENAI:
            raise ImportError(
                "OpenAI package is not installed. Please install it with 'pip install openai>=1.0.0'"
            )

        self.client = OpenAI(
            base_url="https://api.openai.com/v1/",
            api_key=api_key,
            organization=organization,
        )

    def generate_completion(
        self,
        model: str,
        prompt: str,
        options: GenerationOptions,
    ) -> CompletionResponse:
        """Generate a text completion using OpenAI.

        Note: OpenAI has deprecated their completions endpoint in favor of chat completions.
        This method uses chat completions with a user message to simulate the older completions behavior.
        """
        # Build options dictionary
        # Map GenerationOptions to OpenAI parameters
        option_mapping = {
            "max_tokens": options.max_tokens,
            "temperature": options.temperature,
            "top_p": options.top_p,
            "stop": options.stop_sequences,
        }

        # Build options dictionary excluding None values
        parsed_opts = {k: v for k, v in option_mapping.items() if v is not None}

        # Handle logprobs parameters
        if options and options.logprobs is True:
            parsed_opts["logprobs"] = True
            if options.top_logprobs is not None:
                parsed_opts["top_logprobs"] = options.top_logprobs

        # Add any OpenAI-specific extensions
        if options and options.extensions:
            openai_extensions = clean_extensions(options.extensions, "x-openai-")
            parsed_opts.update(openai_extensions)

        # Use chat completions as a replacement for the deprecated completions endpoint
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **parsed_opts,
        )

        print("Received response from OpenAI client.")

        # Extract the response text
        text = response.choices[0].message.content or ""

        # Map the OpenAI finish reason to our standardized format
        finish_reason_map = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
        }
        finish_reason = finish_reason_map.get(
            response.choices[0].finish_reason, FinishReason.STOP
        )

        # Process logprobs if requested and available
        logprobs = None
        if options and options.logprobs and hasattr(response.choices[0], "logprobs"):
            logprobs_data = response.choices[0].logprobs

            # Transform OpenAI's logprobs format to our standardized format
            if logprobs_data:
                token_logprobs = {}

                # Map tokens to their logprobs
                if hasattr(logprobs_data, "content") and logprobs_data.content:
                    for token_info in logprobs_data.content:
                        if hasattr(token_info, "token") and hasattr(
                            token_info, "logprob"
                        ):
                            token_logprobs[token_info.token] = token_info.logprob

                if token_logprobs:
                    logprobs = LogProbs(token_logprobs=token_logprobs)

        # Create the standardized response
        return CompletionResponse(
            id=uuid.uuid4(),
            model=response.model,
            text=text,
            finish_reason=finish_reason,
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            provider_info={
                "openai_id": response.id,
                "created": response.created,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
            },
            logprobs=logprobs,  # Include the logprobs in the response
        )

    def generate_chat(
        self,
        model: str,
        messages: list[Message],
        options: GenerationOptions,
    ) -> ChatResponse:
        """Generate a chat response using OpenAI."""
        # Convert our message format to OpenAI format
        parsed_msgs = []
        for msg in messages:
            openai_msg = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                openai_msg["name"] = msg.name
            parsed_msgs.append(openai_msg)

        # Build options dictionary
        # Map GenerationOptions to OpenAI parameters
        option_mapping = {
            "max_tokens": options.max_tokens,
            "temperature": options.temperature,
            "top_p": options.top_p,
            "stop": options.stop_sequences,
        }

        # Build options dictionary excluding None values
        parsed_opts = {k: v for k, v in option_mapping.items() if v is not None}

        # Handle logprobs parameters
        if options and options.logprobs is True:
            parsed_opts["logprobs"] = True
            if options.top_logprobs is not None:
                parsed_opts["top_logprobs"] = options.top_logprobs

        # Add any OpenAI-specific extensions
        if options and options.extensions:
            openai_extensions = clean_extensions(options.extensions, "x-openai-")
            parsed_opts.update(openai_extensions)

        # Make the API call
        response = self.client.chat.completions.create(
            model=model, messages=parsed_msgs, **parsed_opts
        )

        # Map the OpenAI finish reason to our standardized format
        finish_reason_map = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
        }
        finish_reason = finish_reason_map.get(
            response.choices[0].finish_reason, FinishReason.STOP
        )

        # Extract the response message
        resp_message = response.choices[0].message

        # Process logprobs if requested and available
        logprobs = None
        if options and options.logprobs and hasattr(response.choices[0], "logprobs"):
            logprobs_data = response.choices[0].logprobs

            # Transform OpenAI's logprobs format to our standardized format
            if logprobs_data:
                token_logprobs = {}

                # Map tokens to their logprobs
                if hasattr(logprobs_data, "content") and logprobs_data.content:
                    for token_info in logprobs_data.content:
                        if hasattr(token_info, "token") and hasattr(
                            token_info, "logprob"
                        ):
                            token_logprobs[token_info.token] = token_info.logprob

                if token_logprobs:
                    logprobs = LogProbs(token_logprobs=token_logprobs)

        # Create the standardized response
        return ChatResponse(
            id=uuid.uuid4(),
            model=response.model,
            message=Message(
                role=Role(resp_message.role),
                content=resp_message.content or "",
                name=getattr(resp_message, "name", None),
            ),
            finish_reason=finish_reason,
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            provider_info={
                "openai_id": response.id,
                "created": response.created,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
            },
            logprobs=logprobs,
        )
