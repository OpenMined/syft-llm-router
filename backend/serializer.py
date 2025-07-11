from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from datetime import datetime

from constant import PricingChargeType, RouterServiceType, RouterType


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
    router_name: str
    output_dir: Path
    router_type: RouterType


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
