# pong_server.py
from __future__ import annotations

import uuid
import json
from typing import Any, Dict, List, Optional

from datetime import datetime, timezone, timedelta
import argparse as arg_parser

from loguru import logger
from pydantic import BaseModel, Field
from syft_event import SyftEvents
from syft_event.types import Request
from syft_core import Client

from permissions_middleware import (
    create_default_permissions,
    update_endpoint_permissions,
)

# --- Pydantic Models ---
class PingRequest(BaseModel):
    """Request to send a ping."""

    msg: str = Field(description="Ping request string")
    ts: datetime = Field(description="Timestamp of the ping request.")


class PongResponse(BaseModel):
    """Response to a ping request."""

    msg: str = Field(description="Ping response string")
    ts: datetime = Field(description="Timestamp of the pong response.")


class GrantRequest(BaseModel):
    """Request to initiate a permission grant workflow."""
    target_endpoints: List[str] = Field(
        description="List of RPC endpoints to grant access to (e.g., ['/ping'])"
    )
    consumer_email: str = Field(description="Email of the consumer requesting/receiving access.")
    producer_email: str = Field(description="Email of the producer of the target endpoints.")


class GrantResponse(BaseModel):
    """Response for a grant request."""
    status: str = Field(description="Status of the grant operation (e.g., 'granted', 'pending_approval').")
    message: str = Field(description="Descriptive message.")
    access_request_id: Optional[str] = Field(
        default=None,
        description="Unique ID for the access request if pending producer approval."
    )


class ApproveRequest(BaseModel):
    """Request to approve a pending access request."""
    access_request_id: str = Field(description="The unique ID of the pending access request (filename).")
    approved_endpoints: Optional[List[str]] = Field(
        default=None,
        description="Optional: List of endpoints to approve. If None, uses original request."
    )


class ApproveResponse(BaseModel):
    """Response for an approval."""
    status: str = Field(description="Status of the approval operation.")
    message: str = Field(description="Status message.")


class RevokeRequest(BaseModel):
    """Request to revoke permissions for a consumer."""
    target_endpoints: List[str] = Field(
        description="List of RPC endpoints to revoke access from (e.g., ['/ping'])"
    )
    consumer_email: str = Field(description="Email of the consumer whose access is being revoked.")
    producer_email: str = Field(description="Email of the producer of the target endpoints.")


class RevokeResponse(BaseModel):
    """Response for a revoke request."""
    status: str = Field(description="Status of the revoke operation.")
    message: str = Field(description="Status message.")


# --- Server Creation ---
def create_server(client: Optional[Client] = None) -> SyftEvents:
    """Create and return the SyftEvents server with the given client."""
    if client is None:
        client = Client.load()
    return SyftEvents("pingpong", client=client)


# --- RPC Handler Functions ---
def pong(ping: PingRequest, ctx: Request, box: SyftEvents) -> PongResponse:
    """Respond to a ping request."""
    logger.info(f"Got ping request from {ctx.sender} - {ping.msg}")
    return PongResponse(
        msg=f"Pong from {box.client.email}",
        ts=datetime.now(timezone.utc),
    )


def grant_access_handler(grant_req: GrantRequest, ctx: Request, box: SyftEvents) -> GrantResponse:
    logger.info(f"Received grant request from '{ctx.sender}' for endpoints {grant_req.target_endpoints} on behalf of consumer '{grant_req.consumer_email}'")

    # TODO: Check if this server is the producer of the requested endpoints
    if grant_req.producer_email != box.client.email:
        logger.warning(
            f"Grant request for {grant_req.target_endpoints} received by wrong producer. "
            f"Expected: {grant_req.producer_email}, Actual: {box.client.email}"
        )
        return GrantResponse(
            status="error",
            message=f"Error: This server ({box.client.email}) is not the owner ({grant_req.producer_email}) of the requested endpoints."
        )

    # TODO: Owner granting access directly
    if ctx.sender == grant_req.producer_email:
        for endpoint in grant_req.target_endpoints:
            update_endpoint_permissions(box, endpoint, grant_req.consumer_email, permission_type="grant")
        logger.info(
            f"Owner '{ctx.sender}' immediately granted access to '{grant_req.consumer_email}' "
            f"for {grant_req.target_endpoints}."
        )
        return GrantResponse(
            status="granted",
            message=f"Access immediately granted by owner to {grant_req.consumer_email} for {grant_req.target_endpoints}."
        )
    # TODO: Consumer requesting access, requires owner approval
    else:
        access_request_id = str(uuid.uuid4())
        access_requests_dir = box.app_rpc_dir / "access_requests"
        access_requests_dir.mkdir(parents=True, exist_ok=True)

        request_file_path = access_requests_dir / f"{access_request_id}.access"
        request_payload = {
            "request_id": access_request_id,
            "consumer_email": grant_req.consumer_email,
            "producer_email": grant_req.producer_email,
            "requested_endpoints": grant_req.target_endpoints,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "status": "pending_owner_approval"
        }
        try:
            request_file_path.write_text(json.dumps(request_payload, indent=2))
            logger.info(
                f"Consumer '{ctx.sender}' requested access for '{grant_req.consumer_email}'. "
                f"Pending producer approval via '{access_request_id}.access'."
            )
            return GrantResponse(
                status="pending_approval",
                message=f"Access request created for owner approval. Request ID: {access_request_id}",
                access_request_id=access_request_id
            )
        except Exception as e:
            logger.error(f"Failed to write access request file '{request_file_path}': {e}")
            return GrantResponse(
                status="error",
                message=f"Failed to create access request file: {e}"
            )


def approve_access_handler(approve_req: ApproveRequest, ctx: Request, box: SyftEvents) -> ApproveResponse:
    logger.info(f"Received approval request from '{ctx.sender}' for ID '{approve_req.access_request_id}'")

    access_request_id = approve_req.access_request_id
    access_requests_dir = box.app_rpc_dir / "access_requests"
    request_file_path = access_requests_dir / f"{access_request_id}.access"
    processed_requests_dir = access_requests_dir / "processed"
    processed_requests_dir.mkdir(parents=True, exist_ok=True)

    if not request_file_path.exists():
        logger.warning(f"Access request file '{request_file_path}' not found or already processed.")
        return ApproveResponse(
            status="error",
            message="Error: Access request file not found or already processed."
        )

    try:
        request_data = json.loads(request_file_path.read_text())

        # TODO: Check if the approver is the owner of this server
        if ctx.sender != box.client.email:
            logger.warning(
                f"Unauthorized approval attempt. Sender '{ctx.sender}' is not server owner '{box.client.email}'."
            )
            return ApproveResponse(
                status="error",
                message="Error: Only the server owner can approve access requests."
            )

        # TODO: Check if the request itself is for this producer
        if request_data.get("producer_email") != box.client.email:
            logger.warning(
                f"Approval request '{access_request_id}' intended for producer '{request_data.get('producer_email')}', "
                f"but received by server '{box.client.email}'."
            )
            return ApproveResponse(
                status="error",
                message=f"Error: This server ({box.client.email}) is not the producer ({request_data.get('producer_email')}) of the requested endpoints."
            )

        # TODO: Check for expiry
        expires_at_str = request_data.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                request_file_path.unlink(missing_ok=True) # Delete expired request
                logger.warning(f"Access request '{access_request_id}' has expired and was removed.")
                return ApproveResponse(
                    status="error",
                    message="Error: The access request has expired."
                )

        consumer_email = request_data["consumer_email"]
        endpoints_to_grant = approve_req.approved_endpoints if approve_req.approved_endpoints else request_data["requested_endpoints"]

        for endpoint in endpoints_to_grant:
            update_endpoint_permissions(box, endpoint, consumer_email, permission_type="grant")

        # TODO: Move the processed request file
        request_file_path.rename(processed_requests_dir / f"{access_request_id}.access")
        logger.info(
            f"Access request '{access_request_id}' approved. "
            f"Permissions granted to '{consumer_email}' for {endpoints_to_grant}."
        )
        return ApproveResponse(
            status="approved",
            message=f"Access request '{access_request_id}' approved. Access granted to {consumer_email} for {endpoints_to_grant}."
        )

    except json.JSONDecodeError:
        logger.error(f"Error: Invalid JSON in access request file '{request_file_path}'.")
        return ApproveResponse(
            status="error",
            message="Error: Invalid JSON in access request file."
        )
    except Exception as e:
        logger.error(f"Error processing approval for '{access_request_id}.access': {e}")
        return ApproveResponse(
            status="error",
            message=f"Error during approval process: {e}"
        )


def revoke_access_handler(revoke_req: RevokeRequest, ctx: Request, box: SyftEvents) -> RevokeResponse:
    logger.info(f"Received revoke request from '{ctx.sender}' for consumer '{revoke_req.consumer_email}' on endpoints {revoke_req.target_endpoints}")

    # TODO: Only the owner can revoke access
    if ctx.sender != box.client.email:
        logger.warning(
            f"Unauthorized revoke attempt. Sender '{ctx.sender}' is not server owner '{box.client.email}'."
        )
        return RevokeResponse(
            status="error",
            message="Error: Only the server owner can revoke access."
        )

    # TODO: Check if this server is the producer of the requested endpoints
    if revoke_req.producer_email != box.client.email:
        logger.warning(
            f"Revoke request for {revoke_req.target_endpoints} received by wrong producer. "
            f"Expected: {revoke_req.producer_email}, Actual: {box.client.email}"
        )
        return RevokeResponse(
            status="error",
            message=f"Error: This server ({box.client.email}) is not the owner ({revoke_req.producer_email}) of the requested endpoints."
        )

    for endpoint in revoke_req.target_endpoints:
        update_endpoint_permissions(box, endpoint, revoke_req.consumer_email, permission_type="revoke")

    logger.info(
        f"Owner '{ctx.sender}' successfully revoked access for '{revoke_req.consumer_email}' "
        f"from {revoke_req.target_endpoints}."
    )
    return RevokeResponse(
        status="revoked",
        message=f"Access revoked for {revoke_req.consumer_email} from {revoke_req.target_endpoints}."
    )


# --- Main Execution ---
if __name__ == "__main__":
    parser = arg_parser.ArgumentParser(description="Pong Server")
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to a custom config.json file"
    )
    args = parser.parse_args()

    client = Client.load(args.config)
    box = create_server(client)
    logger.info(f"Running as user: {client.email}")

    # Define all RPC endpoints
    all_rpc_endpoints = ["/ping", "/grant", "/approve", "/revoke"]
    public_endpoints = ["/grant"]
    access_requests_dir_name = "access_requests"

    # Register the handlers
    @box.on_request("/ping")
    def ping_handler(ping: PingRequest, ctx: Request) -> PongResponse:
        return pong(ping, ctx, box)

    @box.on_request("/grant")
    def grant_handler(grant_req: GrantRequest, ctx: Request) -> GrantResponse:
        return grant_access_handler(grant_req, ctx, box)

    @box.on_request("/approve")
    def approve_handler(approve_req: ApproveRequest, ctx: Request) -> ApproveResponse:
        return approve_access_handler(approve_req, ctx, box)

    @box.on_request("/revoke")
    def revoke_handler(revoke_req: RevokeRequest, ctx: Request) -> RevokeResponse:
        return revoke_access_handler(revoke_req, ctx, box)

    # Apply default permissions
    create_default_permissions(
        box=box,
        producer_email=client.email,
        all_rpc_endpoints=all_rpc_endpoints,
        public_endpoints=public_endpoints,
        additional_public_dirs=[access_requests_dir_name]
    )

    try:
        logger.info(f"Running RPC server for: {box.app_rpc_dir}")
        box.run_forever()
    except Exception as e:
        logger.critical(f"Server crashed: {e}", exc_info=True)