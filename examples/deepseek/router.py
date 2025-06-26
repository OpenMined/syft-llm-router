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


class DeepSeekLLMRouter(BaseLLMRouter):
    """Implementation of the BaseLLMRouter for DeepSeek API.

    This implementation allows access to DeepSeek models via the DeepSeek API.
    """

    def __init__(self, api_key: str):
        """Initialize the DeepSeek client.

        Args:
            api_key: The DeepSeek API key.
        """
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.allowed_models = ["deepseek-chat", "deepseek-coder", "deepseek"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _validate_model(self, model: str) -> str:
        """Validate that the model is allowed and return the full model name.

        Args:
            model: The model identifier.

        Returns:
            The full model name for DeepSeek.

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
            "deepseek": "deepseek-chat",
            "deepseek-chat": "deepseek-chat",
            "deepseek-coder": "deepseek-coder",
        }

        return model_mapping.get(model, model)

    def _map_finish_reason(self, finish_reason: str) -> FinishReason:
        """Map DeepSeek finish reason to our FinishReason enum.

        Args:
            finish_reason: The finish reason from DeepSeek.

        Returns:
            The corresponding FinishReason enum value.
        """
        mapping = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
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
            "prompt": prompt,
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
                payload["stop"] = options.stop_sequences

        # Make the API request
        response = requests.post(
            f"{self.base_url}/completions", headers=self.headers, json=payload
        )

        # Handle errors
        response.raise_for_status()

        # Parse the response
        response_data = response.json()

        # Extract usage information
        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        # Extract the generated text and other information
        text = response_data.get("choices", [{}])[0].get("text", "")

        finish_reason_str = response_data.get("choices", [{}])[0].get("finish_reason")
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

        # Convert our Message objects to DeepSeek format
        deepseek_messages = []
        for message in messages:
            deepseek_message = {
                "role": message.role.value,
                "content": message.content,
            }
            if message.name:
                deepseek_message["name"] = message.name
            deepseek_messages.append(deepseek_message)

        # Prepare the request payload
        payload = {
            "model": full_model_name,
            "messages": deepseek_messages,
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
                payload["stop"] = options.stop_sequences
            if options.logprobs is not None:
                payload["logprobs"] = options.logprobs
                payload["top_logprobs"] = (
                    options.top_logprobs if options.top_logprobs is not None else 5
                )

        # Make the API request
        response = requests.post(
            f"{self.base_url}/chat/completions", headers=self.headers, json=payload
        )

        # Handle errors
        response.raise_for_status()

        # Parse the response
        response_data = response.json()

        # Extract usage information
        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        # Extract the generated message and other information
        choice = response_data.get("choices", [{}])[0]
        message_data = choice.get("message", {})

        # Create the Message object
        generated_message = Message(
            role=Role(message_data.get("role", "assistant")),
            content=message_data.get("content", ""),
            name=message_data.get("name"),
        )

        # Get finish reason
        finish_reason_str = choice.get("finish_reason")
        finish_reason = (
            self._map_finish_reason(finish_reason_str) if finish_reason_str else None
        )

        logprobs = None

        if "logprobs" in choice:
            try:
                logprobs = choice["logprobs"]["content"][0]["top_logprobs"]
                logprobs = self.__map_logprobs(logprobs)
            except (KeyError, TypeError, IndexError):
                pass

        # Create and return the ChatResponse
        return ChatResponse(
            id=uuid.uuid4(),
            model=model,
            message=generated_message,
            finish_reason=finish_reason,
            usage=usage,
            provider_info={"raw_response": response_data},
            logprobs=logprobs,
        )

    def __map_logprobs(self, logprobs: list[dict]) -> LogProbs:
        """Map DeepSeek logprobs to our LogProbs enum.

        Args:
            logprobs: The logprobs from DeepSeek.

        Returns:
            A LogProbs object containing the token logprobs.
        """

        token_to_logprobs = {}
        for logprob in logprobs:
            token_to_logprobs[logprob["token"]] = logprob["logprob"]

        return LogProbs(token_logprobs=token_to_logprobs)


if __name__ == "__main__":
    import os

    router = DeepSeekLLMRouter(
        api_key=os.getenv("DEEPSEEK_API_KEY"),  # Replace with your DeepSeek API key
    )

    # Example: Generate a completion
    completion_response = router.generate_completion(
        model="deepseek-chat",
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
        model="deepseek-chat",
        messages=messages,
        options=GenerationOptions(max_tokens=100, temperature=0.7),
    )

    print(f"Chat response ID: {chat_response.id}")
    print(f"Assistant's response: {chat_response.message.content}")
    print(f"Token usage: {chat_response.usage}") 