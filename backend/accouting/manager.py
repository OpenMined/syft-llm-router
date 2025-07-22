from syft_core.config import SyftClientConfig
from .schemas import AccountingConfig, UserAccount, UserAccountView
from syft_accounting_sdk import UserClient, ServiceException
from fastapi import HTTPException


class AccountingManager:
    """Accounting manager."""

    def __init__(
        self,
        syftbox_config: SyftClientConfig,
        accounting_config: AccountingConfig,
    ):
        self.syftbox_config = syftbox_config
        self.accounting_config = accounting_config

    @property
    def client(self) -> UserClient:
        """Get user client."""
        return UserClient(
            self.accounting_config.email,
            self.accounting_config.password,
            self.accounting_config.url,
        )

    def get_or_create_user_account(self) -> UserAccount:
        """Get or create user account."""
        try:
            user, password = self.client.create_user(
                url=self.accounting_config.url,
                email=self.accounting_config.email,
                password=self.accounting_config.password,
            )
        except ServiceException as e:
            raise HTTPException(
                f"Failed to create user account: {e}",
                status_code=500,
            )

        return UserAccount(
            id=user.id,
            email=user.email,
            balance=user.balance,
            password=password,
        )

    def get_user_account(self) -> UserAccountView:
        """Get user account information."""
        user = self.client.get_user_info()

        return UserAccountView(
            id=user.id,
            email=user.email,
            balance=user.balance,
        )

    def create_txn_token(self, recipient_email: str) -> str:
        """Create a transaction token for a user email using given user authentication."""
        return self.client.create_transaction_token(recipientEmail=recipient_email)
