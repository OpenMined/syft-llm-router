from typing import Optional
from syft_core.config import SyftClientConfig
from .schemas import (
    AccountingConfig,
    UserAccount,
    UserAccountView,
    TransactionToken,
    TransactionHistory,
    TransactionDetail,
    PaginatedTransactionHistory,
    PaginationInfo,
    TransactionSummary,
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

    def get_user_transactions(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> PaginatedTransactionHistory:
        """Get user transactions with pagination and optional status filtering."""
        try:
            transactions = self.client.get_transaction_history()
            total_credited = 0
            total_debited = 0
            txn_details = []

            # Filter transactions
            filtered_transactions = []
            for transaction in transactions:
                # Apply status filter
                if status and status != "all":
                    if transaction.status.value.lower() != status.lower():
                        continue

                filtered_transactions.append(transaction)

            # Calculate totals for filtered transactions
            for transaction in filtered_transactions:
                if transaction.senderEmail == self.accounting_config.email:
                    total_debited += transaction.amount
                if transaction.recipientEmail == self.accounting_config.email:
                    total_credited += transaction.amount

            # Apply pagination
            total_transactions = len(filtered_transactions)
            total_pages = (total_transactions + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_transactions = filtered_transactions[start_idx:end_idx]

            # Calculate counts for all transactions (not just current page)
            completed_count = sum(
                1
                for t in filtered_transactions
                if t.status.value.lower() == "completed"
            )
            pending_count = sum(
                1 for t in filtered_transactions if t.status.value.lower() == "pending"
            )
            total_spent = sum(
                t.amount
                for t in filtered_transactions
                if t.status.value.lower() == "completed"
            )

            # Convert to TransactionDetail objects
            for transaction in paginated_transactions:
                txn_details.append(
                    TransactionDetail(
                        id=transaction.id,
                        created_at=transaction.createdAt,
                        sender_email=transaction.senderEmail,
                        recipient_email=transaction.recipientEmail,
                        status=transaction.status.value.lower(),  # Convert to lowercase to match frontend expectations
                        amount=transaction.amount,
                    )
                )

            # Create the transaction history data
            transaction_history = TransactionHistory(
                transactions=txn_details,
                total_credits=total_credited,
                total_debits=total_debited,
            )

            # Create pagination info
            pagination_info = PaginationInfo(
                total=total_transactions,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

            # Create summary info
            summary_info = TransactionSummary(
                completed_count=completed_count,
                pending_count=pending_count,
                total_spent=total_spent,
            )

            return PaginatedTransactionHistory(
                data=transaction_history,
                pagination=pagination_info,
                summary=summary_info,
            )
        except ServiceException as e:
            raise APIException(
                f"Failed to get user transactions: {e}",
                status_code=e.status_code,
            )
