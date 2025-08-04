from datetime import datetime
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from uuid import UUID, uuid4
from typing import Optional


class AccountingCredentialsModel(SQLModel, table=True):
    """Database model for storing accounting service credentials."""

    __tablename__ = "accounting_credentials"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: EmailStr
    accounting_service_url: str
    password: str
    organization: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    active: bool = Field(default=False)
