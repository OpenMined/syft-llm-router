from datetime import datetime
from fastapi import APIRouter, Query
from datetime import datetime
from .manager import AccountingManager
from .schemas import (
    UserAccountView,
    TransactionToken,
    PaginatedTransactionHistory,
    AnalyticsResponse,
)
from fastapi import HTTPException
from shared.exceptions import APIException


def build_accounting_api(accounting_manager: AccountingManager) -> APIRouter:
    """Build accounting API router."""

    router = APIRouter(prefix="/account")

    @router.post("/token/create", response_model=TransactionToken)
    async def create_txn_token(recipient_email: str) -> TransactionToken:
        try:
            return accounting_manager.create_txn_token(recipient_email)
        except APIException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/info", response_model=UserAccountView)
    async def get_account_info() -> UserAccountView:
        try:
            return accounting_manager.get_user_account()
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
