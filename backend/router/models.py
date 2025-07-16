from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import JSON

from .constants import RouterType, RouterServiceType, PricingChargeType


class Router(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(unique=True, index=True)
    router_type: RouterType

    services: list["RouterService"] = Relationship(back_populates="router")
    router_metadata: Optional["RouterMetadata"] = Relationship(back_populates="router")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published: bool = Field(default=False)
    author: str


class RouterMetadata(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    summary: str
    description: str
    tags: list[str] = Field(sa_type=JSON)
    code_hash: str
    router_id: UUID = Field(foreign_key="router.id")
    router: "Router" = Relationship(back_populates="router_metadata")


class RouterService(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    type: RouterServiceType
    enabled: bool = Field(default=False)

    router_id: UUID = Field(foreign_key="router.id")
    router: "Router" = Relationship(back_populates="services")

    pricing: float = Field(default=0.0, ge=0.0)
    charge_type: PricingChargeType = Field(default=PricingChargeType.PER_REQUEST)
