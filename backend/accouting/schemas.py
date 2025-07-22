from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from accountingSDK.core import TransactionStatus


class AccountingConfig(BaseModel):
    """Accounting configuration."""

    email: str
    password: str
    url: str


class User(BaseModel):
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
