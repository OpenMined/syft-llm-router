from pathlib import Path
from typing import Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from .constants import PricingChargeType, RouterServiceType, RouterType


# DTOs for Repository Layer (can be used with .from_orm())
class RouterService(BaseModel):
    """DTO for router service data from repository"""

    id: Optional[UUID] = None
    type: RouterServiceType
    enabled: bool
    pricing: float
    charge_type: PricingChargeType

    class Config:
        from_attributes = True


class RouterMetadata(BaseModel):
    """DTO for router metadata from repository"""

    id: Optional[UUID] = None
    summary: str
    description: str
    tags: List[str]
    code_hash: str

    class Config:
        from_attributes = True


class Router(BaseModel):
    """DTO for router data from repository"""

    id: Optional[UUID] = None
    name: str
    router_type: RouterType
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published: bool
    author: str
    services: List[RouterService]
    router_metadata: Optional[RouterMetadata] = None

    class Config:
        from_attributes = True


class RouterCreate(BaseModel):
    """DTO for creating a router"""

    name: str
    router_type: RouterType
    author: str
    services: List[RouterService]
    published: bool = False


class RouterUpdate(BaseModel):
    """DTO for updating a router"""

    published: Optional[bool] = None
    services: Optional[List[RouterService]] = None
    router_metadata: Optional[RouterMetadata] = None


class ServiceOverview(BaseModel):
    type: RouterServiceType
    pricing: float
    charge_type: PricingChargeType = Field(default=PricingChargeType.PER_REQUEST)
    enabled: bool


class PublishRouterRequest(BaseModel):
    router_name: str
    summary: str
    description: str
    tags: list[str]
    services: list[ServiceOverview]


class CreateRouterRequest(BaseModel):
    name: str
    router_type: RouterType
    services: list[RouterServiceType]


class CreateRouterResponse(BaseModel):
    router: Router
    output_dir: Path


class RouterOverview(BaseModel):
    name: str
    published: bool
    summary: str
    author: str
    services: list[ServiceOverview]


class RouterList(BaseModel):
    routers: list[RouterOverview]


class RouterMetadataResponse(BaseModel):
    summary: str
    description: str
    tags: list[str]
    code_hash: str
    author: str
    # endpoints: Optional[dict[str, Any]] = None


class RouterDetails(BaseModel):
    name: str
    published: bool
    services: Optional[list[ServiceOverview]] = None
    metadata: Optional[RouterMetadataResponse] = None
    endpoints: Optional[dict[str, Any]] = None


class ProjectMetadata(BaseModel):
    """Metadata for a published project."""

    project_name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Project description")
    summary: str = Field(..., description="Project summary")
    tags: list[str] = Field(default_factory=list, description="Project tags")
    services: list[ServiceOverview] = Field(
        default_factory=list, description="Pricing information"
    )
    code_hash: str = Field(..., description="SHA256 hash of all Python files")
    version: str = Field(..., description="Project version")
    documented_endpoints: Optional[dict[str, Any]] = Field(
        None, description="API endpoints documentation"
    )
    publish_date: datetime = Field(..., description="Publication date")
    author: str = Field(..., description="Author email")
    schema_path: Optional[str] = Field(None, description="Path to RPC schema file")


class RouterServiceStatus(BaseModel):
    name: str
    status: str
    url: Optional[str] = None


class RouterRunStatus(BaseModel):
    url: Optional[str] = None
    status: str
    services: list[RouterServiceStatus]
