from datetime import datetime
from typing import Optional

from loguru import logger
from shared.exceptions import APIException
from syft_accounting_sdk import ServiceException, UserClient
from syft_core.config import SyftClientConfig

from .repository import AccountingRepository
from .schemas import (
    AccountingConfig,
    AnalyticsResponse,
    AnalyticsSummary,
    DailyMetrics,
    PaginatedTransactionHistory,
    PaginationInfo,
    TransactionDetail,
    TransactionHistory,
    TransactionSummary,
    TransactionToken,
    UserAccount,
    UserAccountView,
)


class AccountingManager:
    """Accounting manager."""

    def __init__(
        self,
        syftbox_config: SyftClientConfig,
        repository: AccountingRepository,
        accounting_config: AccountingConfig,
    ):
        self.syftbox_config = syftbox_config
        self.repository = repository
        self.accounting_config = accounting_config

    @property
    def client(self) -> UserClient:
        """Get a user client."""
        credentials = self.repository.get_active_credentials(
            accounting_service_url=self.accounting_config.url,
        )
        if credentials is None:
            raise APIException(
                f"No active credentials found for {self.accounting_config.url}",
                status_code=404,
            )
        return UserClient(
            url=self.accounting_config.url,
            email=credentials.email,
            password=credentials.password,
        )

    def create_user_on_service(
        self,
        email: str,
        organization: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserAccount:
        """Create a user account on the service."""
        try:
            user, user_pwd = UserClient.create_user(
                url=self.accounting_config.url,
                organization=organization,
                email=email,
                password=password,
            )
        except ServiceException as e:
            logger.error(
                f"Failed to create user account: {e.message} with {e.status_code}"
            )
            if e.status_code == 409:
                raise APIException(
                    f"User account already exists: {e.message}",
                    status_code=e.status_code,
                )
            else:
                raise APIException(
                    f"Failed to create user account: {e.message} with {e.status_code}",
                    status_code=e.status_code,
                )
        return user, user_pwd

    def add_or_update_credentials(
        self,
        email: str,
        organization: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserAccount:
        """Add or update user account credentials to the repository."""

        try:
            credentials = self.repository.add_or_update_credentials(
                email=email,
                password=password,
                accounting_service_url=self.accounting_config.url,
                organization=organization,
            )
        except Exception as e:
            logger.error(f"Failed to add or update credentials: {e}")
            raise APIException(
                f"Failed to add or update credentials: {e}",
                status_code=500,
            )

        try:
            user_info = self.client.get_user_info()
        except ServiceException as e:
            raise APIException(
                f"Failed to get user info: {e}",
                status_code=e.status_code,
            )

        return UserAccount(
            email=credentials.email,
            organization=credentials.organization,
            balance=user_info.balance,
            password=credentials.password,
        )

    def get_current_account_info(self) -> UserAccountView:
        """Get current account info."""
        try:
            user_info = self.client.get_user_info()
        except ServiceException as e:
            raise APIException(
                f"Failed to get user info: {e}",
                status_code=e.status_code,
            )
        return UserAccountView(
            email=user_info.email,
            organization=user_info.organization,
            balance=user_info.balance,
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
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PaginatedTransactionHistory:
        """Get user transactions with pagination and optional status filtering."""
        try:
            transactions = self.client.get_transaction_history()
            total_credited = 0
            total_debited = 0
            txn_details = []

            # Filter transactions
            filtered_transactions = []
            # sort transactions by created_at datetime
            transactions.sort(key=lambda x: x.createdAt, reverse=True)
            for transaction in transactions:
                if start_date and transaction.createdAt <= start_date:
                    continue
                if end_date and transaction.createdAt >= end_date:
                    continue

                # Apply status filter
                if status and status != "all":
                    if transaction.status.value.lower() != status.lower():
                        continue

                filtered_transactions.append(transaction)

            # Calculate totals for completed transactions only (to match balance calculation)
            for transaction in filtered_transactions:
                if transaction.status.value.lower() == "completed":
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

    def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AnalyticsResponse:
        """Get analytics data with daily metrics and summary."""
        try:
            transactions = self.client.get_transaction_history()

            # Filter transactions by date if provided
            filtered_transactions = []
            for transaction in transactions:
                if start_date and transaction.createdAt < start_date:
                    continue
                if end_date and transaction.createdAt > end_date:
                    continue
                filtered_transactions.append(transaction)

            # Group transactions by date
            daily_data = {}
            for transaction in filtered_transactions:
                date_str = transaction.createdAt.strftime("%Y-%m-%d")
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        "query_count": 0,
                        "total_earned": 0.0,
                        "total_spent": 0.0,
                        "completed_count": 0,
                        "pending_count": 0,
                    }

                daily_data[date_str]["query_count"] += 1

                if transaction.status.value.lower() == "completed":
                    daily_data[date_str]["completed_count"] += 1
                    if transaction.recipientEmail == self.accounting_config.email:
                        daily_data[date_str]["total_earned"] += transaction.amount
                    if transaction.senderEmail == self.accounting_config.email:
                        daily_data[date_str]["total_spent"] += transaction.amount
                elif transaction.status.value.lower() == "pending":
                    daily_data[date_str]["pending_count"] += 1

            # Convert to DailyMetrics objects
            daily_metrics = []
            for date_str, data in sorted(daily_data.items()):
                net_profit = data["total_earned"] - data["total_spent"]
                daily_metrics.append(
                    DailyMetrics(
                        date=date_str,
                        query_count=data["query_count"],
                        total_earned=data["total_earned"],
                        total_spent=data["total_spent"],
                        net_profit=net_profit,
                        completed_count=data["completed_count"],
                        pending_count=data["pending_count"],
                    )
                )

            # Calculate summary statistics
            total_days = len(daily_metrics)
            total_queries = sum(m.query_count for m in daily_metrics)
            total_earned = sum(m.total_earned for m in daily_metrics)
            total_spent = sum(m.total_spent for m in daily_metrics)
            total_profit = total_earned - total_spent
            total_completed = sum(m.completed_count for m in daily_metrics)

            avg_daily_queries = total_queries / total_days if total_days > 0 else 0
            avg_daily_earned = total_earned / total_days if total_days > 0 else 0
            avg_daily_spent = total_spent / total_days if total_days > 0 else 0
            avg_daily_profit = total_profit / total_days if total_days > 0 else 0
            success_rate = (
                (total_completed / total_queries * 100) if total_queries > 0 else 0
            )

            summary = AnalyticsSummary(
                total_days=total_days,
                avg_daily_queries=avg_daily_queries,
                avg_daily_earned=avg_daily_earned,
                avg_daily_spent=avg_daily_spent,
                avg_daily_profit=avg_daily_profit,
                total_queries=total_queries,
                total_earned=total_earned,
                total_spent=total_spent,
                total_profit=total_profit,
                success_rate=success_rate,
            )

            return AnalyticsResponse(
                daily_metrics=daily_metrics,
                summary=summary,
            )

        except ServiceException as e:
            raise APIException(
                f"Failed to get analytics: {e}",
                status_code=e.status_code,
            )
