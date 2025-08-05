from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class AccountingConfig(BaseModel):
    """Accounting configuration."""

    url: str


class UserAccount(BaseModel):
    """User account information."""

    email: EmailStr
    balance: float = Field(ge=0.0, default=0.0)
    password: str
    organization: Optional[str] = None


class UserAccountView(BaseModel):
    """User account view (without password)."""

    email: EmailStr
    balance: float = Field(ge=0.0, default=0.0)
    organization: Optional[str] = None


class TransactionToken(BaseModel):
    """Transaction token for payment."""

    token: str
    recipient_email: str


class TransactionDetail(BaseModel):
    """Transaction detail information."""

    id: str
    amount: float
    created_at: datetime
    sender_email: EmailStr
    recipient_email: EmailStr
    status: str


class TransactionHistory(BaseModel):
    """Transaction history response."""

    transactions: List[TransactionDetail]
    total_credits: float
    total_debits: float


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionSummary(BaseModel):
    """Transaction summary statistics."""

    completed_count: int
    pending_count: int
    total_spent: float


class PaginatedTransactionHistory(BaseModel):
    """Paginated transaction history with summary statistics."""

    data: TransactionHistory
    pagination: PaginationInfo
    summary: TransactionSummary


# Analytics Schemas
class DailyMetrics(BaseModel):
    """Daily metrics for analytics."""

    date: str
    query_count: int
    total_earned: float
    total_spent: float
    net_profit: float
    completed_count: int
    pending_count: int


class AnalyticsSummary(BaseModel):
    """Analytics summary statistics."""

    total_days: int
    avg_daily_queries: float
    avg_daily_earned: float
    avg_daily_spent: float
    avg_daily_profit: float
    total_queries: int
    total_earned: float
    total_spent: float
    total_profit: float
    success_rate: float


class AnalyticsResponse(BaseModel):
    """Analytics response with daily metrics and summary."""

    daily_metrics: List[DailyMetrics]
    summary: AnalyticsSummary
