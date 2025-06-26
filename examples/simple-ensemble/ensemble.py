import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from syft_core import Client
from syft_llm_router.schema import ChatResponse
from syft_rpc import rpc
from syft_rpc.rpc_db import (
    SyftBulkFuture,
    delete_bulk_future,
    get_bulk_future,
    save_bulk_future,
)


class ModelInfo(BaseModel):
    name: str
    datasite: str
    app_name: str
    endpoint: str
    model_kwargs: dict


PUNCT_TBL = dict.fromkeys(
    i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith("P")
)


class MCQPrompt:
    CHOICES = ["A", "B", "C", "D"]

    @staticmethod
    def format(question, choices):
        prompt = question
        for idx, opt in enumerate(choices):
            choice = MCQPrompt.CHOICES[idx]
            prompt += f"\n{choice}. {opt}"

        prompt += "\nAnswer:"

        return prompt


DATASITE_1 = "shubhamrouter1@openmined.org"
DATASITE_2 = "shubhamrouter2@openmined.org"

DATASITE_1_CONFIG = {
    "model": "mixtral",
    "app_name": "routers/mixtral",
}

DATASITE_2_CONFIG = {
    "model": "phi-4",
    "app_name": "routers/phi4router",
}

NAMESPACE = "ensemble"


DATASITE_TO_MODEL_MAP = {DATASITE_1: DATASITE_1_CONFIG, DATASITE_2: DATASITE_2_CONFIG}

DEFAULT_CHAT_TIMEOUT = 60  # secs


class MCQBasedEnsemble:
    def __init__(self, client_config: Optional[Path] = None):
        self.system_prompt = "Limit your answer to the final result. Do not explain."
        self.client = (
            Client.load() if client_config is None else Client.load(client_config)
        )
        self.awaiting_futures = []
        self.chat_timeout = DEFAULT_CHAT_TIMEOUT

    def send_chat_message(self, question: str, choices: list[str]):
        if len(choices) > len(MCQPrompt.CHOICES):
            raise ValueError("")

        user_prompt = MCQPrompt.format(question, choices)

        # user message
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        request_data = {
            "messages": messages,
            "options": {
                "temperature": 0.7,
                "max_tokens": 150,
                "top_p": 1.0,
                "logprobs": True,
                "top_logprobs": 5,
            },
        }

        bk_id = self._make_rpc_call(request_data, [DATASITE_1, DATASITE_2])

        return {"chat_id": bk_id}

    def _make_rpc_call(self, request_data: dict, datasites: list):
        futures = []

        for datasite in datasites:
            print(f"Sending request to {datasite}")
            config = DATASITE_TO_MODEL_MAP.get(datasite)

            if config is None:
                raise ValueError(f"Models from {datasite} datasite are not supported. ")

            model_name = config.get("model")
            app_name = config.get("app_name")

            url = rpc.make_url(datasite=datasite, app_name=app_name, endpoint="chat")

            print(f"Sending request to {url}")

            request_data["model"] = model_name
            future = rpc.send(
                client=self.client,
                url=url,
                body=request_data,
                expiry="5m",
                cache=True,
            )

            futures.append(future)

        bk_future = SyftBulkFuture(futures=futures)
        if get_bulk_future(bulk_id=bk_future.id):
            ValueError("Request already exists !!")

        save_bulk_future(bk_future, namespace=NAMESPACE)

        return bk_future.id

    def get_chat_response(self, chat_id, timeout: int = DEFAULT_CHAT_TIMEOUT):
        bk_future = get_bulk_future(bulk_id=chat_id)

        if bk_future is None:
            raise ValueError(f"No chat exists for id: {chat_id}")

        responses = bk_future.gather_completed(timeout=timeout)

        if len(bk_future.pending) > 0:
            ValueError("Waiting for response. Not all models have responded back.")

        if bk_future.all_failed:
            delete_bulk_future(bulk_id=bk_future.id)
            ValueError("Failed to get results from the models. Please try again.")

        chat_responses = []
        for response in responses:
            chat_resp = response.model(ChatResponse)
            chat_responses.append(chat_resp)

        print(f"Chat responses received: {len(chat_responses)}")
        return chat_responses

    def poll_response(self, chat_id):
        """Generate chat result."""
        response = self.get_chat_response(chat_id=chat_id, timeout=120)
        ensemble_result = self.apply_ensembling(response)
        return self.format_result(ensemble_result)

    @staticmethod
    def normalize_logprobs(logprobs: dict[str, float]) -> dict[str, float]:
        # Convert log probabilities to probabilities
        probs = {token: math.exp(logprob) for token, logprob in logprobs.items()}

        # Normalize to sum to 1
        total = sum(probs.values())
        if total > 0:  # Avoid division by zero
            normalized_probs = {token: prob / total for token, prob in probs.items()}
            # Convert back to log probabilities
            normalized_logprobs = {
                token: math.log(prob) if prob > 0 else -100.0
                for token, prob in normalized_probs.items()
            }
            return normalized_logprobs
        else:
            # If all probabilities are effectively zero, return the original
            return logprobs

    def apply_ensembling(
        self,
        responses: list[ChatResponse],
        weights: Optional[dict] = None,
    ):
        model_choice_logprobs = {}
        for response in responses:
            model_name = response.model
            logprob_map = response.logprobs.token_logprobs
            if logprob_map is None or len(logprob_map) == 0:
                # Use the model's output as a fallback
                choice_logprobs = self.fallback_to_output(response.message)
            else:
                # Extract choice logprobs from the list of logprobs
                choice_logprobs = self.extract_choice_logprobs(
                    logprob_map, MCQPrompt.CHOICES
                )

            # Normalize if requested
            choice_logprobs = self.normalize_logprobs(choice_logprobs)

            model_choice_logprobs[model_name] = choice_logprobs

        logprobs = self.ensemble_logprobs(model_choice_logprobs, weights)

        # Get the prediction from the ensembled logprobs
        ensemble_prediction = self.get_prediction_from_logprobs(logprobs)

        return ensemble_prediction

    @staticmethod
    def fallback_to_output(
        raw_output: str, choices: list = MCQPrompt.CHOICES
    ) -> dict[str, float]:
        # Initialize all choices with low probability
        choice_logprobs = {choice: -100.0 for choice in choices}

        # If output exists and is one of the choices, give it high probability
        if raw_output is not None and raw_output in choices:
            # Give the chosen answer a high probability (log(0.9) ≈ -0.1)
            choice_logprobs[raw_output] = -0.1

            # Distribute the remaining probability among other choices
            remaining_prob = (
                math.log(0.1 / (len(choices) - 1)) if len(choices) > 1 else -100.0
            )
            for choice in choices:
                if choice != raw_output:
                    choice_logprobs[choice] = remaining_prob

        return choice_logprobs

    @staticmethod
    def extract_choice_logprobs(
        logprob_map: dict[str, float], choices=MCQPrompt.CHOICES
    ) -> dict[str, float]:
        # Initialize with very low logprob values (log(0) would be -inf)
        choice_logprobs = {choice: -100.0 for choice in choices}

        # If logprobs is None, return the initialized default values
        if logprob_map is None:
            return choice_logprobs

        # Search through all tokens in the logprobs list
        for token, logprob in logprob_map.items():
            # Skip if the individual entry is None
            if logprob is None:
                continue

            # Clean the token for better matching
            # Clean the token for better matching
            clean_token = token.strip()

            # Remove punctuation for more flexible matching
            clean_token_no_punct = clean_token.translate(PUNCT_TBL)

            # Check if this token matches any of our choices
            for choice in choices:
                # Check for direct match (case-insensitive)
                if clean_token.upper() == choice.upper():
                    choice_logprobs[choice] = max(choice_logprobs[choice], logprob)
                    continue

                # Check for parenthesized format (A) or (a)
                paren_match = re.search(r"\(([A-Za-z])\)", clean_token, re.IGNORECASE)
                if paren_match and paren_match.group(1).upper() == choice.upper():
                    choice_logprobs[choice] = max(choice_logprobs[choice], logprob)
                    continue

                # Ignore punctuation and ignore case
                if clean_token_no_punct.upper() == choice.upper():
                    choice_logprobs[choice] = max(choice_logprobs[choice], logprob)
                    continue

        return choice_logprobs

    @staticmethod
    def ensemble_logprobs(
        model_logprobs: dict[str, dict[str, float]],
        models: Optional[list[str]] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> dict[str, float]:
        if models is None:
            models = list(model_logprobs.keys())

        if weights is None:
            # Default to equal weights
            weights = {model: 1.0 / len(models) for model in models}

        # Initialize ensemble with all possible choices
        all_choices = set()
        for model in models:
            if model in model_logprobs:
                all_choices.update(model_logprobs[model].keys())

        # Convert logprobs to probabilities, apply weights, and sum
        ensemble_probs = {choice: 0.0 for choice in all_choices}

        for model in models:
            model_weight = weights.get(model, 0.0)
            if model_weight <= 0 or model not in model_logprobs:
                continue

            # Get this model's logprobs, filling in missing values with very low probability
            model_choice_logprobs = model_logprobs[model]

            # Convert to probabilities, apply weight, and add to ensemble
            for choice in all_choices:
                logprob = model_choice_logprobs.get(
                    choice, -100.0
                )  # Default for missing choices
                prob = math.exp(logprob)
                ensemble_probs[choice] += prob * model_weight

                # Try if taking a max over an average
                # ensemble_probs[choice] = max(ensemble_probs[choice], prob * model_weight)

        # Convert back to logprobs
        ensemble_logprobs = {
            choice: math.log(prob) if prob > 0 else -100.0
            for choice, prob in ensemble_probs.items()
        }

        return ensemble_logprobs

    @staticmethod
    def get_prediction_from_logprobs(logprobs: dict[str, float]) -> str:
        if not logprobs:
            return ""  # Return empty string if logprobs is empty
        return max(logprobs.items(), key=lambda x: x[1])[0]

    def format_result(self, ensemble_result):
        return f"Assistant: Your correct answer is: {ensemble_result}"


if __name__ == "__main__":
    ensemble = MCQBasedEnsemble()

    question = "What is the capital of France?"
    choices = ["Paris", "London", "Berlin", "Madrid"]
    response = ensemble.send_chat_message(
        question=question,
        choices=choices,
    )

    print("Chat id: ", response)

    chat_id = response["chat_id"]
    # chat_id = UUID("c400c8b9-6d3d-4ef3-bb57-54abb526b113")

    print("User:\n", MCQPrompt.format(question=question, choices=choices))
    print(ensemble.poll_response(chat_id=chat_id))
