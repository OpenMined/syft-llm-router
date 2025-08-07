from datetime import datetime
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from shared.exceptions import APIException

from .manager import AccountingManager
from .schemas import (
    AnalyticsResponse,
    PaginatedTransactionHistory,
    TransactionToken,
    UserAccount,
    UserAccountView,
)


def build_accounting_api(accounting_manager: AccountingManager) -> APIRouter:
    """Build accounting API router."""

    router = APIRouter(prefix="/account")

    @router.post("/token/create", response_model=TransactionToken, tags=["syftbox"])
    async def create_txn_token(recipient_email: str = Query(..., description="Email of the recipient")) -> TransactionToken:
        try:
            # URL decode the email parameter in case it's encoded
            decoded_email = unquote(recipient_email)
            return accounting_manager.create_txn_token(decoded_email)
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/info", response_model=UserAccountView)
    async def get_account_info() -> UserAccountView:
        try:
            return accounting_manager.get_current_account_info()
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/url", response_model=str)
    async def get_accounting_service_url() -> str:
        return accounting_manager.accounting_config.url

    @router.post("/credential/create", response_model=UserAccount)
    async def add_account_credentials(
        email: str,
        organization: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserAccount:
        """Add account credentials to the accounting service.

        Try creating a user on the accounting service.
        - If the user already exists, raise an error.
        - If the user does not exist, create the user and add the user account info to the repository.
        """
        try:
            # Try creating a user on the accounting service
            user, user_pwd = accounting_manager.create_user_on_service(
                email, organization, password
            )

            # Add the user account info to the repository
            user_account = accounting_manager.add_or_update_credentials(
                user.email, user.organization, user_pwd
            )
            return user_account
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    @router.post("/credential/update", response_model=UserAccount)
    async def update_account_credentials(
        email: str,
        organization: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserAccount:
        """Update account credentials."""
        if not organization and not password:
            raise HTTPException(
                status_code=400, detail="Either organization or password is required"
            )
        try:
            return accounting_manager.add_or_update_credentials(
                email, organization, password
            )
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/history", response_model=PaginatedTransactionHistory)
    async def get_transaction_history(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(
            10, ge=1, le=100, description="Number of items per page"
        ),
        status: str = Query(
            None, description="Filter by status (completed, pending, failed)"
        ),
        start_date: datetime = Query(
            None, description="Filter by start date (ISO format)"
        ),
        end_date: datetime = Query(None, description="Filter by end date (ISO format)"),
    ) -> PaginatedTransactionHistory:
        try:
            return accounting_manager.get_user_transactions(
                page, page_size, status, start_date, end_date
            )
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/analytics", response_model=AnalyticsResponse)
    async def get_analytics(
        start_date: datetime = Query(
            None, description="Filter by start date (ISO format)"
        ),
        end_date: datetime = Query(None, description="Filter by end date (ISO format)"),
    ) -> AnalyticsResponse:
        try:
            return accounting_manager.get_analytics(start_date, end_date)
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    return router
