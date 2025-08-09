from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import jwt
from pydantic import BaseModel, EmailStr, Field, model_validator

from .constants import (
    DelegateControlType,
    PricingChargeType,
    RouterServiceType,
    RouterType,
)


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
    delegate_email: Optional[EmailStr] = None

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
    delegate_email: Optional[EmailStr] = None


class RouterList(BaseModel):
    routers: list[RouterOverview]


class RouterMetadataResponse(BaseModel):
    summary: str
    description: str
    tags: list[str]
    code_hash: str
    author: str
    delegate_email: Optional[EmailStr] = None
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
    delegate_email: Optional[EmailStr] = Field(
        None,
        description="Datasite email to whom router is delegated to.",
    )
    delegate_control_types: Optional[List[DelegateControlType]] = Field(
        None,
        description="Types of control the delegate has over the router.",
    )

    @classmethod
    def load_from_file(cls, file_path: Path) -> "ProjectMetadata":
        """Load project metadata from a file."""
        return cls.model_validate_json(file_path.read_text())

    def save_to_file(self, file_path: Path) -> None:
        """Save project metadata to a file."""
        file_path.write_text(self.model_dump_json())


class RouterServiceStatus(BaseModel):
    name: str
    status: str
    url: Optional[str] = None


class RouterRunStatus(BaseModel):
    url: Optional[str] = None
    status: str
    services: list[RouterServiceStatus]


class AvailableDelegatesResponse(BaseModel):
    """List of available delegates from their public directory."""

    delegates: List[EmailStr]


class DelegateRouterRequest(BaseModel):
    """Request to delegate a router to a delegate."""

    router_name: str
    delegate_email: EmailStr


class DelegateRouterResponse(BaseModel):
    """Response to delegate a router to a delegate."""

    router: Router


class RevokeDelegationRequest(BaseModel):
    """Request to revoke delegation of a router."""

    router_name: str


class RevokeDelegationResponse(BaseModel):
    """Response to revoke delegation of a router."""

    router_name: str
    delegate_email: EmailStr


class ServicePricingUpdate(BaseModel):
    """Data for updating pricing of a service."""

    service_type: RouterServiceType
    new_pricing: float
    new_charge_type: PricingChargeType


class ControlDataOptions(BaseModel):
    """Options for control data.

    TODO: Later with more control types, we can add more options here and make them
    optional. For now, we only have pricing updates.
    """

    pricing_updates: Optional[List[ServicePricingUpdate]] = None

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_update(cls, values):
        """Ensure at least one type of update is provided."""
        if isinstance(values, dict):
            has_updates = any(
                values.get(field) is not None and values.get(field) != []
                for field in [
                    "pricing_updates",
                    # TODO: Add more control types here
                ]
            )
            if not has_updates:
                raise ValueError("At least one type of update must be provided")
        return values


class DelegateControlRequest(BaseModel):
    """Request to delegate control of a router."""

    router_name: str
    delegate_email: EmailStr
    control_type: DelegateControlType
    control_data: ControlDataOptions
    delegate_access_token: str
    reason: Optional[str] = None


class DelegateControlResponse(BaseModel):
    """Response to delegate control of a router."""

    success: bool
    router_name: str
    message: Optional[str] = None


class DelegateControlAuditCreate(BaseModel):
    """Data for creating a delegate control audit."""

    router_name: str
    delegate_email: EmailStr
    control_type: DelegateControlType
    control_data: Dict[str, Any]
    reason: Optional[str] = None


class DelegateControlAuditView(BaseModel):
    """Data for a delegate control audit log."""

    router_name: str
    delegate_email: EmailStr
    control_type: DelegateControlType
    control_data: Dict[str, Any]
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DCALogsResponse(BaseModel):
    """View of a delegate control audit logs."""

    audit_logs: List[DelegateControlAuditView]


class JWTTokenPayload(BaseModel):
    """Payload for a JWT token."""

    router_name: str
    router_author: str
    delegate_email: EmailStr
    control_type: DelegateControlType
    created_at: datetime

    def encode(self, secret_key: str) -> str:
        """Generate a JWT token."""
        return jwt.encode(self.model_dump(mode="json"), secret_key, algorithm="HS256")

    @classmethod
    def decode(cls, access_token: str, secret_key: str) -> "JWTTokenPayload":
        """Decode a JWT token."""
        return cls.model_validate(
            jwt.decode(access_token, secret_key, algorithms=["HS256"])
        )
