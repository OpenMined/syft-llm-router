import uuid
from typing import Optional

import requests
from syft_llm_router.router import BaseLLMRouter
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


class ClaudeLLMRouter(BaseLLMRouter):
    """Implementation of the BaseLLMRouter for Anthropic Claude API.

    This implementation allows access to Claude models via the Anthropic API.
    """

    def __init__(self, api_key: str):
        """Initialize the Anthropic client.

        Args:
            api_key: The Anthropic API key.
        """
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.allowed_models = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude"]
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

    def _validate_model(self, model: str) -> str:
        """Validate that the model is allowed and return the full model name.

        Args:
            model: The model identifier.

        Returns:
            The full model name for Anthropic.

        Raises:
            ValueError: If the model is not allowed.
        """
        if model not in self.allowed_models:
            allowed_models_str = ", ".join(self.allowed_models)
            raise ValueError(
                f"Model '{model}' is not allowed. Allowed models: {allowed_models_str}"
            )

        # Map short names to full model names
        model_mapping = {
            "claude": "claude-3-sonnet-20240229",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307"
        }

        return model_mapping.get(model, model)

    def _map_finish_reason(self, finish_reason: str) -> FinishReason:
        """Map Anthropic finish reason to our FinishReason enum.

        Args:
            finish_reason: The finish reason from Anthropic.

        Returns:
            The corresponding FinishReason enum value.
        """
        mapping = {
            "end_turn": FinishReason.STOP,
            "max_tokens": FinishReason.LENGTH,
            "stop_sequence": FinishReason.STOP,
        }
        return mapping.get(finish_reason, None)

    def generate_completion(
        self,
        model: str,
        prompt: str,
        options: Optional[GenerationOptions] = None,
    ) -> CompletionResponse:
        """Generate a text completion based on a prompt.

        Args:
            model: The model identifier to use for generation.
            prompt: The input text to generate from.
            options: Additional parameters for the generation.

        Returns:
            A CompletionResponse object containing the generated text.

        Raises:
            ValueError: If the model is not allowed.
            requests.RequestException: If there's an issue with the API request.
        """
        full_model_name = self._validate_model(model)

        # Prepare the request payload
        payload = {
            "model": full_model_name,
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens": 1000,  # Default max tokens
        }

        # Add options if provided
        if options:
            if options.max_tokens is not None:
                payload["max_tokens"] = options.max_tokens
            if options.temperature is not None:
                payload["temperature"] = options.temperature
            if options.top_p is not None:
                payload["top_p"] = options.top_p
            if options.stop_sequences is not None:
                payload["stop_sequences"] = options.stop_sequences

        # Make the API request
        response = requests.post(
            f"{self.base_url}/complete", headers=self.headers, json=payload
        )

        # Handle errors
        response.raise_for_status()

        # Parse the response
        response_data = response.json()

        # Extract usage information
        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )

        # Extract the generated text and other information
        text = response_data.get("completion", "")

        finish_reason_str = response_data.get("stop_reason")
        finish_reason = (
            self._map_finish_reason(finish_reason_str) if finish_reason_str else None
        )

        # Create and return the CompletionResponse
        return CompletionResponse(
            id=uuid.uuid4(),
            model=model,
            text=text,
            finish_reason=finish_reason,
            usage=usage,
            provider_info={"raw_response": response_data},
        )

    def generate_chat(
        self,
        model: str,
        messages: list[Message],
        options: Optional[GenerationOptions] = None,
    ) -> ChatResponse:
        """Generate a chat response based on a conversation history.

        Args:
            model: The model identifier to use for chat.
            messages: Array of message objects representing the conversation.
            options: Additional parameters for the generation.

        Returns:
            A ChatResponse object containing the generated message.

        Raises:
            ValueError: If the model is not allowed.
            requests.RequestException: If there's an issue with the API request.
        """
        full_model_name = self._validate_model(model)

        # Convert our Message objects to Anthropic format
        anthropic_messages = []
        for message in messages:
            # Skip system messages as they need to be handled differently
            if message.role == Role.SYSTEM:
                continue
                
            anthropic_message = {
                "role": "user" if message.role == Role.USER else "assistant",
                "content": message.content,
            }
            anthropic_messages.append(anthropic_message)

        # Prepare the request payload
        payload = {
            "model": full_model_name,
            "messages": anthropic_messages,
            "max_tokens": 1000,  # Default max tokens
        }

        # Add options if provided
        if options:
            if options.max_tokens is not None:
                payload["max_tokens"] = options.max_tokens
            if options.temperature is not None:
                payload["temperature"] = options.temperature
            if options.top_p is not None:
                payload["top_p"] = options.top_p
            if options.stop_sequences is not None:
                payload["stop_sequences"] = options.stop_sequences

        # Make the API request
        response = requests.post(
            f"{self.base_url}/messages", headers=self.headers, json=payload
        )

        # Handle errors
        response.raise_for_status()

        # Parse the response
        response_data = response.json()

        # Extract usage information
        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )

        # Extract the generated message and other information
        content = response_data.get("content", [{}])[0]
        message_data = content.get("text", "")

        # Create the Message object
        generated_message = Message(
            role=Role.ASSISTANT,
            content=message_data,
        )

        # Get finish reason
        finish_reason_str = response_data.get("stop_reason")
        finish_reason = (
            self._map_finish_reason(finish_reason_str) if finish_reason_str else None
        )

        # Create and return the ChatResponse
        return ChatResponse(
            id=uuid.uuid4(),
            model=model,
            message=generated_message,
            finish_reason=finish_reason,
            usage=usage,
            provider_info={"raw_response": response_data},
        )


if __name__ == "__main__":
    import os

    router = ClaudeLLMRouter(
        api_key=os.getenv("ANTHROPIC_API_KEY"),  # Replace with your Anthropic API key
    )

    # Example: Generate a completion
    completion_response = router.generate_completion(
        model="claude-3-sonnet",
        prompt="What is 1+1 ?",
        options=GenerationOptions(max_tokens=500, temperature=0.7),
    )

    print(f"Completion ID: {completion_response.id}")
    print(f"Generated text: {completion_response.text}")
    print(f"Token usage: {completion_response.usage}")

    # Example: Generate a chat response
    messages = [
        Message(role=Role.SYSTEM, content="You are a helpful assistant."),
        Message(role=Role.USER, content="What's the capital of France?"),
    ]

    chat_response = router.generate_chat(
        model="claude-3-sonnet",
        messages=messages,
        options=GenerationOptions(max_tokens=100, temperature=0.7),
    )

    print(f"Chat response ID: {chat_response.id}")
    print(f"Assistant's response: {chat_response.message.content}")
    print(f"Token usage: {chat_response.usage}") 