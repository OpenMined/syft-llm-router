# permissions_middleware.py
from __future__ import annotations

import yaml
from typing import Any, Optional, List, Dict
from loguru import logger

PUBLIC_READ_WRITE_RULE = {
    "pattern": '**',
    "access": {
        "read": ["*"],
        "write": ["*"]
    }
}

OWNER_ONLY_RULE_TEMPLATE = {
    "pattern": '**',
    "access": {
        "read": [],
        "write": [],
        "admin": []
    }
}

def create_default_permissions(
    box,
    producer_email: str,
    all_rpc_endpoints: List[str],
    public_endpoints: Optional[List[str]] = None,
    additional_public_dirs: Optional[List[str]] = None
):
    """
    Ensures that all endpoint-specific syft.pub.yaml files are set to owner-only access
    by default (relying on file system owner permissions), with exceptions for public_endpoints.

    Args:
        box: The SyftEvents instance.
        producer_email: The email of the owner.
        all_rpc_endpoints: A list of all RPC endpoint strings (e.g., ['/ping', '/grant']).
        public_endpoints: A list of endpoint strings (e.g., '/grant')
                          that should remain publicly accessible (wildcard user).
        additional_public_dirs: A list of directory names within app_rpc_dir that should be public.
    """
    if public_endpoints is None:
        public_endpoints = []
    if additional_public_dirs is None:
        additional_public_dirs = []

    logger.info(f"Applying default permissions. Owner: {producer_email}, Public Endpoints: {public_endpoints}, Public Dirs: {additional_public_dirs}")

    # TODO: Iterate over all explicitly registered RPC endpoints
    # Use the endpoint strings to construct paths, avoiding __rpc access
    for endpoint_str in all_rpc_endpoints:
        endpoint_path_obj = box.app_rpc_dir / endpoint_str.lstrip("/").rstrip("/")
        endpoint_path_obj.mkdir(exist_ok=True, parents=True)

        local_perm_file = endpoint_path_obj / "syft.pub.yaml"

        rules_to_write: List[Dict[str, Any]] = []

        if endpoint_str in public_endpoints:
            logger.info(f"Endpoint '{endpoint_str}' is explicitly public. Setting wildcard user permissions.")
            rules_to_write.append(PUBLIC_READ_WRITE_RULE.copy())
        else:
            logger.info(f"Endpoint '{endpoint_str}' is owner-only by default. Creating explicit empty rules.")
            rules_to_write.append(OWNER_ONLY_RULE_TEMPLATE.copy())

        content_to_write = yaml.dump({"rules": rules_to_write}, default_flow_style=False, sort_keys=False)

        try:
            local_perm_file.write_text(content_to_write)
            logger.info(f"Created/Overwrote local syft.pub.yaml for '{endpoint_str}': {local_perm_file}")
        except Exception as e:
            logger.error(f"Error creating/overwriting local syft.pub.yaml for '{endpoint_str}': {e}")

    # TODO: Handle additional public directories like 'access_requests'
    for dir_name in additional_public_dirs:
        dir_path_obj = box.app_rpc_dir / dir_name
        dir_path_obj.mkdir(exist_ok=True, parents=True)
        local_perm_file = dir_path_obj / "syft.pub.yaml"

        rules_to_write: List[Dict[str, Any]] = []
        logger.info(f"Directory '{dir_name}' is explicitly public. Setting wildcard user permissions.")
        rules_to_write.append(PUBLIC_READ_WRITE_RULE.copy())

        content_to_write = yaml.dump({"rules": rules_to_write}, default_flow_style=False, sort_keys=False)
        try:
            local_perm_file.write_text(content_to_write)
            logger.info(f"Created/Overwrote local syft.pub.yaml for '{dir_name}': {local_perm_file}")
        except Exception as e:
            logger.error(f"Error creating/overwriting local syft.pub.yaml for '{dir_name}': {e}")


def update_endpoint_permissions(box, endpoint_name: str, user_email: str, permission_type: str = "grant"):
    """
    Dynamically updates permissions for a specific endpoint for a given user in syft.pub.yaml.
    Assumes file owner always has permission.

    Args:
        box: The SyftEvents instance.
        endpoint_name: The string representation of the endpoint (e.g., '/ping').
        user_email: The email of the user to grant/revoke permissions for.
        permission_type: 'grant' to add permissions, 'revoke' to remove.
    """
    endpoint_path = box.app_rpc_dir / endpoint_name.lstrip("/").rstrip("/")
    perm_file = endpoint_path / "syft.pub.yaml"

    if not endpoint_path.exists():
        logger.warning(f"Endpoint path '{endpoint_path}' does not exist. Cannot update permissions.")
        return

    current_content: Dict[str, Any] = {"rules": []}
    if perm_file.exists():
        try:
            with open(perm_file, 'r') as f:
                loaded_content = yaml.safe_load(f)
            if isinstance(loaded_content, dict) and "rules" in loaded_content and isinstance(loaded_content["rules"], list):
                current_content = loaded_content
            else:
                logger.warning(f"Existing syft.pub.yaml for '{endpoint_name}' is malformed or empty. Resetting.")
        except yaml.YAMLError as e:
            logger.error(f"Error reading existing permissions for '{endpoint_name}': {e}. Starting with empty permissions.")
        except FileNotFoundError:
            logger.info(f"syft.pub.yaml not found for '{endpoint_name}'. Initializing with empty rules.")
    else:
        logger.info(f"syft.pub.yaml not found for '{endpoint_name}'. Initializing with empty rules.")


    current_rules = current_content["rules"]

    # TODO: Look for a rule that applies to all files in the endpoint directory (pattern '**')
    target_rule = None
    for rule in current_rules:
        if rule.get("pattern") == '**' and isinstance(rule.get("access"), dict):
            target_rule = rule
            break

    # TODO: If no suitable rule found, create a new one based on the owner-only template
    if target_rule is None:
        target_rule = OWNER_ONLY_RULE_TEMPLATE.copy()
        current_rules.append(target_rule)
        logger.info(f"No existing rule found for '{endpoint_name}'. Creating a new owner-only rule.")

    # TODO: Ensure access lists exist within the target rule
    access_dict = target_rule.setdefault("access", {})
    read_list = access_dict.setdefault("read", [])
    write_list = access_dict.setdefault("write", [])
    admin_list = access_dict.setdefault("admin", []) # For future extensibility

    if not isinstance(read_list, list): access_dict["read"] = []
    if not isinstance(write_list, list): access_dict["write"] = []
    if not isinstance(admin_list, list): access_dict["admin"] = []


    # TODO: Modify permissions based on type
    if permission_type == "grant":
        if user_email not in access_dict["read"]:
            access_dict["read"].append(user_email)
        if user_email not in access_dict["write"]:
            access_dict["write"].append(user_email)
        logger.info(f"Granted read/write permissions for '{user_email}' on '{endpoint_name}'.")

    elif permission_type == "revoke":
        if user_email in access_dict["read"]:
            access_dict["read"].remove(user_email)
        if user_email in access_dict["write"]:
            access_dict["write"].remove(user_email)
        if user_email in access_dict["admin"]:
            access_dict["admin"].remove(user_email)
        logger.info(f"Revoked permissions for '{user_email}' on '{endpoint_name}'.")

    else:
        logger.warning(f"Unknown permission type: '{permission_type}'. No action taken for '{endpoint_name}'.")
        return

    # TODO: Write back the modified permissions
    try:
        with open(perm_file, 'w') as f:
            yaml.dump(current_content, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully updated syft.pub.yaml for '{endpoint_name}'.")
    except Exception as e:
        logger.error(f"Error writing updated permissions for '{endpoint_name}': {e}")