from loguru import logger
from syft_core import Client
from syft_llm_router.error import RouterError
from syft_llm_router.schema import ChatResponse, CompletionResponse
from syft_rpc import rpc
import accounting
from accountingSDK import UserClient as AccountingUserClient

APP_NAME = "routers/claude"


def test_chat(
    client: Client,
    accounting_client: AccountingUserClient,
    model: str,
    datasite: str,
    user_message: str,
    system_message: str = None,
):
    """
    Send a simple chat request to an LLM through the Syft LLM Router.

    Parameters
    ----------
    client : Client
        The Syft client instance.
    accounting_client : AccountingUserClient
        The accounting client instance.
    model : str
        The model to use.
    datasite : str
        The datasite to send the request to (e.g., "username@domain.org").
    user_message : str
        The message from the user to send to the model.
    system_message : str, optional
        An optional system message to include.

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

    token = accounting_client.create_transaction_token(recipientEmail=datasite)
    print(f"Token: {token}")
    # Create request
    request_data = {
        "model": model,
        "accounting_token": token,
        "messages": messages,
        "options": {
            "temperature": 0.7,
            "max_tokens": 150,
            "top_p": 1.0,
        },
    }
    print(f"Request data: {request_data}")

    url = (rpc.make_url(datasite=datasite, app_name=APP_NAME, endpoint="chat"),)
    logger.debug(url)

    try:
        # Send the request
        future = rpc.send(
            client=client,
            url=rpc.make_url(datasite=datasite, app_name=APP_NAME, endpoint="chat"),
            body=request_data,
            expiry="5m",
            cache=True,
        )

        response = future.wait()
        response.raise_for_status()
        try:
            chat_response = response.model(ChatResponse)
            return chat_response.message.content
        except Exception:
            return response.model(RouterError)

    except Exception as e:
        logger.error(f"Error sending chat request: {e}")
        return None


def test_completion(client: Client, datasite: str, promt: str, model: str = "claude-3-sonnet"):
    """
    Send a completion request to an LLM through the Syft LLM Router.

    Parameters
    ----------
    client : Client
        The Syft client instance.
    datasite : str
        The datasite to send the request to.
    promt : str
        The prompt to send to the model.
    model : str, optional
        The model to use, by default "claude-3-sonnet".

    Returns
    -------
    str or None
        The model's response text, or None if an error occurred.
    """
    # Create request
    request_data = {
        "model": model,
        "prompt": promt,
        "options": {"temperature": 0.7, "max_tokens": 150, "top_p": 1.0},
    }

    try:
        # Send the request
        future = rpc.send(
            client=client,
            url=rpc.make_url(
                datasite=datasite, app_name=APP_NAME, endpoint="completions"
            ),
            body=request_data,
            expiry="5m",
            cache=True,
        )

        response = future.wait()
        response.raise_for_status()
        try:
            completion_response = response.model(CompletionResponse)
            return completion_response.text
        except Exception:
            return response.model(RouterError)

    except Exception as e:
        logger.error(f"Error sending completion request: {e}")
        return None


# Example usage
if __name__ == "__main__":
    client = Client.load()
    accounting_client: AccountingUserClient = accounting.get_or_init_user_client(
        syftbox_config_path="~/.syftbox/config.json",
        accounting_config_path="~/.syftbox/accounting-config.json",
    )

    print("Client", client.email)

    # This is the datasite where the LLM Routing service is running
    # Change this to the datasite of the LLM Routing service you want to use
    datasite = client.email

    print("Test chat....")

    # Multiple choice question example
    question = """
    How many legs does a spider have?

    A. 0
    B. 2
    C. 8
    D. 6

    Answer:
    """
    import time

    st = time.time()
    response = test_chat(
        client=client,
        accounting_client=accounting_client,
        datasite=datasite,
        user_message=question,
        system_message="Limit your answer to the final result. Explain your answer.",
        model="claude-3-sonnet",
    )

    et = time.time()
    print(f"Time taken: {et - st} seconds")
    print(f"Response: {response}")

    print("\nTest completion....")

    # Completion example
    prompt = "What is 1+1 ?"

    st = time.time()
    # Send the request
    completion_response = test_completion(
        client=client,
        datasite=datasite,
        promt=prompt,
        model="claude-3-sonnet",
    )
    et = time.time()
    print(f"Time taken: {et - st} seconds")
    print(f"Completion Response: {completion_response}") 