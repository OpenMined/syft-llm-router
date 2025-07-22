from fastapi import APIRouter
from .manager import AccountingManager
from .schemas import UserAccountView, TransactionToken
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

    return router
