# grant_request.py
from __future__ import annotations

import sys
import time
import argparse as arg_parser
from loguru import logger
from pydantic import BaseModel, Field
from typing import List, Optional

from syft_core import Client
from syft_rpc import rpc


# Define the request and response models (can be copied from pong_server.py)
class GrantRequest(BaseModel):
    target_endpoints: List[str] = Field(description="List of RPC endpoints to grant access to (e.g., ['/ping'])")
    consumer_email: str = Field(description="Email of the consumer requesting/receiving access.")
    producer_email: str = Field(description="Email of the producer of the target endpoints.")

class GrantResponse(BaseModel):
    status: str = Field(description="Status of the grant operation (e.g., 'granted', 'pending_approval').")
    message: str = Field(description="Descriptive message.")
    access_request_id: Optional[str] = Field(default=None)


def send_grant_request(
    target_datasite_email: str,
    client: Client,
    target_endpoints: List[str],
    consumer_email: str,
    producer_email: str
):
    logger.info(f"Sending grant request to {target_datasite_email} from {client.email}")
    start = time.time()
    grant_body = GrantRequest(
        target_endpoints=target_endpoints,
        consumer_email=consumer_email,
        producer_email=producer_email
    )

    future = rpc.send(
        url=rpc.make_url(datasite=target_datasite_email, app_name="ensemble", endpoint="grant"),
        body=grant_body,
        expiry="5m",
        cache=True,
        client=client,
    )
    logger.debug(f"Request: {future.request}")

    try:
        response = future.wait(timeout=300)
        response.raise_for_status()
        grant_response = response.model(GrantResponse)
        logger.info(f"Grant Response: {grant_response.status} - {grant_response.message}")
        logger.info(f"Response: {grant_response}. Time taken: {time.time() - start}")
        if grant_response.access_request_id:
            logger.info(f"Access Request ID: {grant_response.access_request_id}")
    except Exception as e:
        logger.error(f"Error sending grant request: {e}")
        raise


def get_datasites(client: Client) -> List[str]:
    return sorted([ds.name for ds in client.datasites.glob("*") if "@" in ds.name])


def valid_datasite(ds: str, client: Client) -> bool:
    return ds in get_datasites(client)


def prompt_input(client: Client, prompt_msg: str) -> Optional[str]:
    while True:
        datasites = get_datasites(client)
        val = input(prompt_msg)
        if prompt_msg.startswith("Enter datasite"):
            if valid_datasite(val, client):
                return val
            else:
                print(f"Invalid datasite: {val}.")
                for d in datasites:
                    print("-", d)
        else:
            return val


def main():
    parser = arg_parser.ArgumentParser(description="Grant Request Client")
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to a custom config.json file for the calling client"
    )
    parser.add_argument(
        "--datasite",
        type=str,
        help="Email of the datasite (producer of the pong server) to send grant request to"
    )
    parser.add_argument(
        "--consumer-email",
        type=str,
        help="Email of the consumer who needs access"
    )
    parser.add_argument(
        "--producer-email",
        type=str,
        help="Email of the producer of the target endpoints (usually the server's email)"
    )
    parser.add_argument(
        "--endpoints",
        nargs='+',
        help="Space-separated list of target endpoints to request access for (e.g., /ping /another)"
    )
    args = parser.parse_args()

    try:
        client = Client.load(args.config)
        print(f"Connected as: {client.email}")

        ds = args.datasite
        if not ds:
            ds = prompt_input(client, "Enter datasite (producer of the pong server): ")
            if not ds:
                logger.error("No datasite provided.")
                sys.exit(1)
        elif not valid_datasite(ds, client):
            print(f"Invalid datasite: {ds}")
            for d in get_datasites(client):
                print("-", d)
            sys.exit(1)

        consumer_email = args.consumer_email
        if not consumer_email:
            consumer_email = prompt_input(client, "Enter consumer email: ")

        producer_email = args.producer_email
        if not producer_email:
            producer_email = prompt_input(client, "Enter producer email (usually the datasite email): ")

        endpoints = args.endpoints
        if not endpoints:
            endpoints_str = prompt_input(client, "Enter target endpoints (space-separated, e.g., /ping /data): ")
            endpoints = endpoints_str.split()

        send_grant_request(ds, client, endpoints, consumer_email, producer_email)

    except KeyboardInterrupt:
        logger.info("bye!")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()