from loguru import logger
from syft_core import Client
from syft_llm_router.schema import ChatRequest, ChatResponse
from syft_rpc import rpc


def send_chat(
    client: Client,
    datasite: str,
    user_message: str,
    system_message: str = None,
    model: str = "gpt-3.5-turbo",
):
    """
    Send a simple chat request to an LLM through the Syft LLM Router.

    Parameters
    ----------
    client : Client
        The Syft client instance.
    datasite : str
        The datasite to send the request to (e.g., "username@domain.org").
    user_message : str
        The message from the user to send to the model.
    system_message : str, optional
        An optional system message to include.
    model : str, optional
        The model to use, by default "gpt-3.5-turbo".

    Returns
    -------
    str or None
        The model's response text, or None if an error occurred.
    """
    # Build messages list
    messages = []

    # Add system message if provided
    if system_message:
        messages.append({"role": "system", "content": system_message})

    # Add user message
    messages.append({"role": "user", "content": user_message})

    # Create request
    request = {
        "model": model,
        "messages": messages,
        "options": {"temperature": 0.7, "max_tokens": 150, "top_p": 1.0},
    }

    try:
        # Send the request
        future = rpc.send(
            client=client,
            url=rpc.make_url(datasite=datasite, app_name="llm", endpoint="chat"),
            body=ChatRequest(**request),
            expiry="5m",
            cache=True,
        )

        response = future.wait()
        response.raise_for_status()
        chat_response = response.model(ChatResponse)

        return chat_response.message.content

    except Exception as e:
        logger.error(f"Error sending chat request: {e}")
        return None


# Example usage
if __name__ == "__main__":
    client = Client.load()

    # This is the datasite where the LLM Routing service is running
    datasite = client.email

    # Multiple choice question example
    question = """
    How many legs does a spider have?

    A. 0
    B. 2
    C. 8
    D. 6

    Answer:
    """

    response = send_chat(
        client=client,
        datasite=datasite,
        user_message=question,
        system_message="Limit your answer to the final result. Explain your answer.",
    )

    print(f"Response: {response}")
