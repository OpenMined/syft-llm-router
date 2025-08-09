from syft_core.client_shim import Client as SyftClient
from .constants import PUBLIC_ROUTER_DIR_NAME, ROUTER_DIR_NAME


def make_user_a_delegate(syftbox_client: SyftClient, current_user: str) -> bool:
    """Make user a delegate.

    This function will make the current user a delegate.
    It will create a delegate file in the current user's public directory.
    """
    router_public_dir = (
        syftbox_client.my_datasite / PUBLIC_ROUTER_DIR_NAME / ROUTER_DIR_NAME
    )
    router_public_dir.mkdir(parents=True, exist_ok=True)
    delegate_file = router_public_dir / f"{current_user}.delegate"
    delegate_file.touch(exist_ok=True)

    delegate_file.write_text(f"{current_user} is now a delegate.")

    return True


def is_user_a_delegate(syftbox_client: SyftClient, current_user: str) -> bool:
    """Check if user is a delegate."""
    router_public_dir = (
        syftbox_client.my_datasite / PUBLIC_ROUTER_DIR_NAME / ROUTER_DIR_NAME
    )
    delegate_file = router_public_dir / f"{current_user}.delegate"
    return delegate_file.exists()
