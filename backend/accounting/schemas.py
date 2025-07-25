from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class AccountingConfig(BaseModel):
    """Accounting configuration."""

    email: str
    password: str
    url: str


class UserAccount(BaseModel):
    """User account."""

    id: str
    email: EmailStr
    balance: float = Field(ge=0.0, default=0.0)
    password: str


class UserAccountView(BaseModel):
    """User account view."""

    id: str
    email: EmailStr
    balance: float = Field(ge=0.0, default=0.0)


class TransactionToken(BaseModel):
    """Transaction token."""

    token: str
    recipient_email: str


class TransactionDetail(BaseModel):
    """Transaction detail."""

    id: str
    amount: float
    created_at: datetime
    sender_email: EmailStr
    recipient_email: EmailStr
    status: str
    amount: float


class TransactionHistory(BaseModel):
    """Transaction history. Returns a list of transactions and the total credited and debited amounts."""

    transactions: list[TransactionDetail]
    total_credits: float
    total_debits: float
