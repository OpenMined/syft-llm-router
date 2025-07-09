from datetime import datetime
from typing import Annotated, Optional
from enum import Enum
from uuid import uuid4, UUID
from fastapi import Depends

from sqlmodel import (
    Field,
    Session,
    SQLModel,
    create_engine,
    Relationship,
)
from sqlalchemy import JSON

from constant import RouterType, RouterServiceType, PricingChargeType


class Router(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(unique=True, index=True)
    router_type: RouterType

    services: list["RouterService"] = Relationship(back_populates="router")
    router_metadata: Optional["RouterMetadata"] = Relationship(back_populates="router")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published: bool = Field(default=False)


class RouterMetadata(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    summary: str
    description: str
    tags: list[str] = Field(sa_type=JSON)
    code_hash: str
    router_id: UUID = Field(foreign_key="router.id")
    router: "Router" = Relationship(back_populates="router_metadata")
    author: str


class RouterService(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    type: RouterServiceType
    enabled: bool = Field(default=False)

    router_id: UUID = Field(foreign_key="router.id")
    router: "Router" = Relationship(back_populates="services")

    pricing: float = Field(default=0.0, ge=0.0)
    charge_type: PricingChargeType = Field(default=PricingChargeType.PER_REQUEST)


sqlite_file_name = "routers.db"

engine = create_engine(f"sqlite:///{sqlite_file_name}")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
