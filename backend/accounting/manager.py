from syft_core.config import SyftClientConfig
from .schemas import (
    AccountingConfig,
    UserAccount,
    UserAccountView,
    TransactionToken,
    TransactionHistory,
    TransactionDetail,
)
from syft_accounting_sdk import UserClient, ServiceException
from shared.exceptions import APIException
from loguru import logger


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
            url=self.accounting_config.url,
            email=self.accounting_config.email,
            password=self.accounting_config.password,
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
            if e.status_code == 409:
                logger.info(f"User account already exists: {e}")
                user = self.client.get_user_info()
                password = self.accounting_config.password
            else:
                raise APIException(
                    f"Failed to create user account: {e}",
                    status_code=e.status_code,
                )

        return UserAccount(
            id=user.id,
            email=user.email,
            balance=user.balance,
            password=password,
        )

    def get_user_account(self) -> UserAccountView:
        """Get user account information."""
        try:
            user = self.client.get_user_info()
        except ServiceException as e:
            raise APIException(
                f"Failed to get user account: {e}",
                status_code=e.status_code,
            )

        return UserAccountView(
            id=user.id,
            email=user.email,
            balance=user.balance,
        )

    def create_txn_token(self, recipient_email: str) -> TransactionToken:
        """Create a transaction token for a user email using given user authentication."""
        try:
            token = self.client.create_transaction_token(recipientEmail=recipient_email)
        except ServiceException as e:
            raise APIException(
                f"Failed to create transaction token: {e}",
                status_code=e.status_code,
            )

        return TransactionToken(token=token, recipient_email=recipient_email)

    def get_user_transactions(self) -> TransactionHistory:
        """Get user transactions. Returns a list of transactions."""
        try:
            transaction_details = self.client.get_transaction_history()
            total_credited = 0
            total_debited = 0
            for transaction in transaction_details:
                transaction_details.append(
                    TransactionDetail(
                        id=transaction.id,
                        created_at=transaction.createdAt,
                        sender_email=transaction.senderEmail,
                        recipient_email=transaction.recipientEmail,
                        status=transaction.status,
                        amount=transaction.amount,
                    )
                )

                if transaction.senderEmail == self.accounting_config.email:
                    total_debited += transaction.amount
                if transaction.recipientEmail == self.accounting_config.email:
                    total_credited += transaction.amount

            return TransactionHistory(
                transactions=transaction_details,
                total_credits=total_credited,
                total_debits=total_debited,
            )
        except ServiceException as e:
            raise APIException(
                f"Failed to get user transactions: {e}",
                status_code=e.status_code,
            )
