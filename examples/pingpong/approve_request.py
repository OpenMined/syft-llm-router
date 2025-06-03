# approve_request.py
from __future__ import annotations

import sys
import time
import argparse as arg_parser
from loguru import logger
from pydantic import BaseModel, Field
from typing import List, Optional

from syft_core import Client
from syft_rpc import rpc


# Define the request and response models
class ApproveRequest(BaseModel):
    access_request_id: str = Field(description="The unique ID of the pending access request (filename).")
    approved_endpoints: Optional[List[str]] = Field(default=None)

class ApproveResponse(BaseModel):
    status: str = Field(description="Status of the approval operation.")
    message: str = Field(description="Status message.")


def send_approve_request(
    target_datasite_email: str,
    client: Client,
    access_request_id: str,
    approved_endpoints: Optional[List[str]] = None
):
    logger.info(f"Sending approve request to {target_datasite_email} from {client.email}")
    start = time.time()
    approve_body = ApproveRequest(
        access_request_id=access_request_id,
        approved_endpoints=approved_endpoints
    )

    future = rpc.send(
        url=rpc.make_url(datasite=target_datasite_email, app_name="ensemble", endpoint="approve"),
        body=approve_body,
        expiry="5m",
        cache=True,
        client=client,
    )
    logger.debug(f"Request: {future.request}")

    try:
        response = future.wait(timeout=300)
        response.raise_for_status()
        approve_response = response.model(ApproveResponse)
        logger.info(f"Approve Response: {approve_response.status} - {approve_response.message}")
    except Exception as e:
        logger.error(f"Error sending approve request: {e}")
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
    parser = arg_parser.ArgumentParser(description="Approve Request Client")
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to a custom config.json file for the producer client"
    )
    parser.add_argument(
        "--datasite",
        type=str,
        help="Email of the datasite (producer of the pong server) to send approve request to"
    )
    parser.add_argument(
        "--request-id",
        type=str,
        required=True,
        help="The unique ID of the pending access request (e.g., from /list_access_requests)"
    )
    parser.add_argument(
        "--approved-endpoints",
        nargs='*',
        help="Optional: Space-separated list of endpoints to approve. If omitted, approves all requested."
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

        send_approve_request(ds, client, args.request_id, args.approved_endpoints)

    except KeyboardInterrupt:
        logger.info("bye!")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()