from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

from .constants import (
    DelegateControlType,
    PricingChargeType,
    RouterServiceType,
    RouterType,
)


class RouterModel(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(unique=True, index=True)
    router_type: RouterType

    services: list["RouterServiceModel"] = Relationship(back_populates="router")
    router_metadata: Optional["RouterMetadataModel"] = Relationship(
        back_populates="router"
    )
    delegate_control_audits: list["DelegateControlAuditModel"] = Relationship(
        back_populates="router"
    )

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published: bool = Field(default=False)
    author: str


class RouterMetadataModel(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    summary: str
    description: str
    tags: list[str] = Field(sa_type=JSON)
    code_hash: str
    router_id: UUID = Field(foreign_key="routermodel.id")
    delegate_email: Optional[str] = Field(default=None, index=True)
    router: "RouterModel" = Relationship(back_populates="router_metadata")


class RouterServiceModel(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    type: RouterServiceType
    enabled: bool = Field(default=False)

    router_id: UUID = Field(
        foreign_key="routermodel.id"
    )  # Fixed: reference correct table name
    router: "RouterModel" = Relationship(back_populates="services")

    pricing: float = Field(default=0.0, ge=0.0)
    charge_type: PricingChargeType = Field(default=PricingChargeType.PER_REQUEST)


class DelegateControlAuditModel(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    router_id: UUID = Field(foreign_key="routermodel.id")
    router: "RouterModel" = Relationship(back_populates="delegate_control_audits")
    delegate_email: EmailStr
    control_type: DelegateControlType
    control_data: Dict[str, Any] = Field(sa_type=JSON)
    reason: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
