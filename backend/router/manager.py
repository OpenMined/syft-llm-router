import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

import jwt
from accounting.repository import AccountingRepository
from generator.common.config import StateFile
from generator.service import (
    ProjectConfig,
    SimplifiedProjectGenerator,
    UserAccountingConfig,
)
from pydantic import EmailStr
from settings.app_settings import settings
from shared.exceptions import APIException
from syft_core import Client as SyftClient
from syft_core.config import SyftClientConfig
from syft_core.permissions import PERM_FILE, SyftPermission

from .constants import PUBLIC_ROUTER_DIR_NAME, ROUTER_DIR_NAME, DelegateControlType
from .models import PricingChargeType, RouterServiceType
from .publish import publish_project, unpublish_project
from .repository import RouterRepository
from .schemas import (
    AvailableDelegatesResponse,
    CreateRouterRequest,
    CreateRouterResponse,
    DCALogsResponse,
    DelegateControlAuditCreate,
    DelegateControlRequest,
    DelegateControlResponse,
    DelegateRouterResponse,
    JWTTokenPayload,
    ServicePricingUpdate,
    ProjectMetadata,
    PublishRouterRequest,
    RevokeDelegationResponse,
    Router,
    RouterCreate,
    RouterDetails,
    RouterList,
    RouterMetadata,
    RouterMetadataResponse,
    RouterOverview,
    RouterRunStatus,
    RouterService,
    RouterServiceStatus,
    RouterUpdate,
    ServiceOverview,
)


class RouterManager:
    def __init__(
        self,
        repository: RouterRepository,
        accounting_repository: AccountingRepository,
        syftbox_config: SyftClientConfig,
        syftbox_client: SyftClient,
        router_app_dir: Path,
        template_dir: Path,
    ):
        self.repository = repository
        self.accounting_repository = accounting_repository
        self.syftbox_config = syftbox_config
        self.syftbox_client = syftbox_client
        self.router_app_dir = router_app_dir
        self.template_dir = template_dir

    def _get_accounting_credentials(self) -> UserAccountingConfig:
        """Get active accounting credentials from database."""

        # Get the accounting service URL from the current user's context
        credentials = self.accounting_repository.get_active_credentials(
            settings.accounting_service_url
        )

        if not credentials:
            raise APIException(
                "No active accounting credentials found. "
                "Please set up your accounting service credentials first.",
                404,
            )

        # Return the credentials as a UserAccountingConfig object
        return UserAccountingConfig(
            url=credentials.accounting_service_url,
            email=credentials.email,
            password=credentials.password,
        )

    def create_router(self, request: CreateRouterRequest) -> CreateRouterResponse:
        """Create a new router app"""
        author = self.get_current_user()

        # Get accounting credentials from database instead of settings
        user_accounting_config = self._get_accounting_credentials()

        config = ProjectConfig(
            project_name=request.name.strip(),
            router_type=request.router_type.value,
            enable_chat=RouterServiceType.CHAT in request.services,
            enable_search=RouterServiceType.SEARCH in request.services,
            syftbox_config=self.syftbox_config,
            user_accounting_config=user_accounting_config,
        )

        generator = SimplifiedProjectGenerator(template_dir=self.template_dir)
        output_dir = self.router_app_dir / config.project_name
        generator.generate_project(config, output_dir=output_dir)

        # Create router services as Pydantic DTOs
        router_services = []
        for service_type in RouterServiceType.all_types():
            enabled = RouterServiceType(service_type) in request.services
            router_services.append(
                RouterService(
                    type=RouterServiceType(service_type),
                    enabled=enabled,
                    pricing=0.0,  # Default pricing
                    charge_type=PricingChargeType.PER_REQUEST,
                )
            )

        # Create router as Pydantic DTO
        router_data = RouterCreate(
            name=config.project_name,
            router_type=request.router_type,
            author=author,
            services=router_services,
            published=False,
        )

        # Let repository handle ORM conversion and persistence
        router = self.repository.create_router(router_data)

        return CreateRouterResponse(
            router=router,
            output_dir=output_dir,
        )

    def publish_router(self, request: PublishRouterRequest) -> dict:
        """Publish a router app"""
        router = self.repository.get_router_by_name(request.router_name)
        if router is None:
            raise APIException(f"Router {request.router_name} not found", 404)

        if router.published:
            raise APIException(f"Router {request.router_name} already published", 400)

        router_dir = self.router_app_dir / request.router_name
        if not router_dir.exists():
            raise APIException(
                f"Router {request.router_name} not found in apps directory", 404
            )

        try:
            metadata, published_path = publish_project(
                project_name=request.router_name,
                project_folder_path=router_dir,
                description=request.description,
                summary=request.summary,
                tags=request.tags,
                services=request.services,
                client_config_path=self.syftbox_config.path,
            )
        except Exception as e:
            raise APIException(
                f"Error publishing router {request.router_name}: {e}", 500
            )

        # Update router using Pydantic DTO
        router_update = RouterUpdate(
            published=True,
            router_metadata=RouterMetadata(
                summary=request.summary,
                description=request.description,
                tags=request.tags,
                code_hash=metadata.code_hash,
            ),
            services=[
                RouterService(
                    type=service.type,
                    enabled=service.enabled,
                    pricing=service.pricing,
                    charge_type=service.charge_type,
                )
                for service in request.services
            ],
        )

        updated_router = self.repository.create_or_update_router(
            request.router_name, router_update
        )
        if updated_router is None:
            raise APIException(f"Failed to update router {request.router_name}", 500)

        return {
            "message": "Router published successfully.",
            "published_path": str(published_path),
        }

    def get_current_user(self) -> str:
        """Get the current user"""
        return self.syftbox_client.email

    def unpublish_router(self, router_name: str) -> dict:
        """Unpublish a router"""
        router = self.repository.get_router_by_name(router_name)
        if router is None or router.author != self.get_current_user():
            raise APIException(
                f"Router {router_name} not found or not owned by {self.get_current_user()}",
                404,
            )

        if not router.published:
            raise APIException(f"Router {router_name} is not published", 400)

        try:
            # Revoke router from delegate
            self.revoke_delegation(router_name)

            # Unpublish router
            unpublish_project(router_name, self.syftbox_config.path)

            # Update router published status
            self.repository.set_published_status(router_name, False)
        except Exception as e:
            raise APIException(f"Error un publishing router {router_name}: {e}", 500)

        return {"message": "Router unpublished successfully."}

    def list_routers(self) -> RouterList:
        """List current datasite routers + all published routers from other datasites"""
        routers = self.repository.get_all_routers()
        all_routers = []

        for router in routers:
            all_routers.append(
                RouterOverview(
                    name=router.name,
                    published=router.published,
                    summary=(
                        router.router_metadata.summary if router.router_metadata else ""
                    ),
                    author=router.author,
                    delegate_email=(
                        router.router_metadata.delegate_email
                        if router.router_metadata
                        else None
                    ),
                    services=[
                        ServiceOverview(
                            type=service.type,
                            pricing=service.pricing,
                            charge_type=service.charge_type,
                            enabled=service.enabled,
                        )
                        for service in router.services
                    ],
                )
            )

        # Fetch published routers from other datasites (requires syftbox client)
        # This involves iterating through datasites and reading metadata.json files
        for datasite in self.syftbox_client.datasites.iterdir():
            # Skip current datasite
            if datasite.name == self.syftbox_client.email:
                continue

            # Get routers directory
            routers_dir = datasite / PUBLIC_ROUTER_DIR_NAME / ROUTER_DIR_NAME

            # Skip if routers directory does not exist
            if not routers_dir.exists():
                continue

            # Iterate through all the routers in the datasite
            for router_dir in routers_dir.iterdir():
                metadata_path = Path(router_dir) / "metadata.json"
                if not metadata_path.exists():
                    continue

                # Load metadata
                metadata = ProjectMetadata.load_from_file(metadata_path)

                all_routers.append(
                    RouterOverview(
                        name=metadata.project_name,
                        published=True,
                        author=metadata.author,
                        summary=metadata.summary,
                        delegate_email=metadata.delegate_email,
                        services=[
                            ServiceOverview(
                                type=service.type,
                                pricing=service.pricing,
                                charge_type=service.charge_type,
                                enabled=service.enabled,
                            )
                            for service in metadata.services
                        ],
                    )
                )

        return RouterList(routers=all_routers)

    def delete_router(self, router_name: str, published: bool) -> dict:
        """Delete a router app"""
        router = self.repository.get_router_by_name(router_name)
        if router is None:
            raise APIException(f"Router {router_name} not found", 404)

        if router.published:
            public_metadata_path = (
                self.syftbox_client.my_datasite
                / PUBLIC_ROUTER_DIR_NAME
                / ROUTER_DIR_NAME
                / router_name
                / "metadata.json"
            )
            public_metadata_path.unlink(missing_ok=True)
        else:
            router_dir = self.router_app_dir / router_name
            if router_dir.exists():
                shutil.rmtree(router_dir, ignore_errors=True)

        deleted = self.repository.delete_router(router_name)
        if not deleted:
            raise APIException(f"Failed to delete router {router_name}", 500)

        return {"message": "Router deleted successfully."}

    def get_router_details(
        self, router_name: str, author: str, published: bool
    ) -> RouterDetails:
        """Fetch the details of a router app"""
        metadata = None
        services = []
        endpoints = {}

        if author == self.get_current_user():
            # Fetch router information from the database
            router = self.repository.get_router_by_name(router_name, published)
            if router is None:
                raise APIException(f"Router {router_name} not found", 404)

            if router.router_metadata:
                metadata = RouterMetadataResponse(
                    summary=router.router_metadata.summary,
                    description=router.router_metadata.description,
                    tags=router.router_metadata.tags,
                    code_hash=router.router_metadata.code_hash,
                    author=router.author,
                    delegate_email=router.router_metadata.delegate_email,
                )

            if router.services:
                for service in router.services:
                    services.append(
                        ServiceOverview(
                            type=service.type,
                            pricing=service.pricing,
                            charge_type=service.charge_type,
                            enabled=service.enabled,
                        )
                    )

            # Load OpenAPI endpoints if available
            endpoints_dir = (
                self.router_app_dir / router_name / f"{router_name}.openapi.json"
            )
            if endpoints_dir.exists():
                endpoints = json.loads(endpoints_dir.read_text())

            published = router.published
        elif published:
            # Fetch router information from the public directory of the datasite (requires syftbox client)
            router_dir = (
                self.syftbox_client.datasites
                / author
                / PUBLIC_ROUTER_DIR_NAME
                / ROUTER_DIR_NAME
                / router_name
            )
            if not router_dir.exists():
                raise APIException(f"Router {router_name} not found", 404)

            metadata_path = router_dir / "metadata.json"

            # Load metadata if it exists
            if metadata_path.exists():
                published_metadata = ProjectMetadata.load_from_file(metadata_path)

                metadata = RouterMetadataResponse(
                    summary=published_metadata.summary,
                    description=published_metadata.description,
                    tags=published_metadata.tags,
                    code_hash=published_metadata.code_hash,
                    author=published_metadata.author,
                    delegate_email=published_metadata.delegate_email,
                )

                endpoints = published_metadata.documented_endpoints

                services = [
                    ServiceOverview(
                        type=service.type,
                        pricing=service.pricing,
                        charge_type=service.charge_type,
                        enabled=service.enabled,
                    )
                    for service in published_metadata.services
                ]
            published = True

        return RouterDetails(
            name=router_name,
            published=published,
            metadata=metadata,
            services=services,
            endpoints=endpoints,
        )

    def get_router_status(self, router_name: str) -> RouterRunStatus:
        """Get the status of the router"""
        router = self.repository.get_router_by_name(router_name)
        if router is None:
            raise APIException(f"Router {router_name} not found", 404)

        state_file_path = self.router_app_dir / router_name / "state.json"
        if not state_file_path.exists():
            return RouterRunStatus(
                status="stopped",
                services=[],
            )

        state_file = StateFile.load(state_file_path)
        services = []

        for service_name, service_state in state_file.services.items():
            services.append(
                RouterServiceStatus(
                    name=service_name,
                    status=service_state.status.value,
                    url=service_state.url,
                )
            )

        if state_file.router.status is None:
            return RouterRunStatus(
                status="stopped",
                services=services,
            )

        return RouterRunStatus(
            url=state_file.router.url,
            status=state_file.router.status.value,
            services=services,
        )

    def router_exists(self, name: str) -> bool:
        """Check if a router with the given name exists."""
        return self.repository.get_router_by_name(name) is not None

    def revoke_delegate_status(self) -> bool:
        """Revoke delegate status.

        This function will revoke the delegate status of the current user.
        It will delete the delegate file from the current user's public directory.
        """
        router_public_dir = (
            self.syftbox_client.my_datasite / PUBLIC_ROUTER_DIR_NAME / ROUTER_DIR_NAME
        )
        delegate_file = router_public_dir / f"{self.get_current_user()}.delegate"
        delegate_file.unlink(missing_ok=True)
        return True

    def get_available_delegates(self) -> AvailableDelegatesResponse:
        """Get list of available delegates.

        This function will list all the datasites that have a delegate file in their public directory.
        Exclude the current user's datasite.
        """
        delegates = []
        for datasite in self.syftbox_client.datasites.iterdir():
            # Skip current user's datasite
            if datasite.name == self.get_current_user():
                continue

            # Check if datasite has a routers directory
            router_public_dir = datasite / PUBLIC_ROUTER_DIR_NAME / ROUTER_DIR_NAME
            if not router_public_dir.exists():
                continue

            # Check if datasite has a delegate file
            delegate_file = router_public_dir / f"{datasite.name}.delegate"
            if not delegate_file.exists():
                continue

            delegates.append(datasite.name)

        return AvailableDelegatesResponse(delegates=delegates)

    def grant_delegate_access(
        self,
        router_name: str,
        delegate_email: EmailStr,
        control_type: DelegateControlType = DelegateControlType.UPDATE_PRICING,
    ) -> DelegateRouterResponse:
        """Grant delegate access to a router.

        This function will grant delegate access to a router.
        It will create a delegate file in the delegate's public directory.
        It will also generate a delegate access token for the delegate.
        """
        router = self.repository.get_router_by_name(router_name)

        if not router.published:
            raise APIException(
                f"Router {router_name} is not published. Please publish it first.",
                400,
            )

        if router.router_metadata.delegate_email is not None:
            raise APIException(
                f"Router {router_name} is already delegated to {router.router_metadata.delegate_email}. "
                "Please revoke the delegation first.",
                400,
            )

        if router.author == delegate_email:
            raise APIException(
                f"{router.author} is already the author of the router {router_name}.",
                400,
            )

        # Check if email is a valid delegate
        router_dir = (
            self.syftbox_client.datasites
            / delegate_email
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
        )
        delegate_file = router_dir / f"{delegate_email}.delegate"
        if not router_dir.exists() or not delegate_file.exists():
            raise APIException(
                f"Email {delegate_email} is not a valid delegate.",
                400,
            )

        # Update router metadata
        router = self.repository.delegate_router(
            router_name,
            delegate_email,
        )

        # Update router published metadata with delegate email
        project_metadata_path = (
            self.syftbox_client.my_datasite
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
            / router_name
            / "metadata.json"
        )

        # Check if router is published
        if not project_metadata_path.exists():
            raise APIException(
                f"Router {router_name} is not published. Please publish it first.",
                400,
            )

        # Update router published metadata with delegate email
        project_metadata = ProjectMetadata.load_from_file(project_metadata_path)
        project_metadata.delegate_email = delegate_email
        project_metadata.delegate_control_types = [DelegateControlType.UPDATE_PRICING]
        project_metadata.save_to_file(project_metadata_path)

        # Generate delegate access token
        self.generate_delegate_access_token(
            router.name,
            router.author,
            delegate_email,
            control_type,
        )

        return DelegateRouterResponse(router=router)

    def generate_delegate_access_token(
        self,
        router_name: str,
        router_author: str,
        delegate_email: EmailStr,
        control_type: DelegateControlType,
    ) -> None:
        """Generate a delegate access token.

        This function will generate a delegate access token for a router.
        It will return the token.
        """

        # Create directory for delegate access token
        access_token_dir = (
            self.syftbox_client.my_datasite
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
            / router_name
            / "token"
        )
        access_token_dir.mkdir(parents=True, exist_ok=True)

        # Set permissions for the directory
        perms_file_path = access_token_dir / PERM_FILE

        if not perms_file_path.exists():
            syft_perms = SyftPermission.create(self.syftbox_client, access_token_dir)
            syft_perms.terminal = True
            syft_perms.add_rule(
                path="**",
                user=delegate_email,
                permission=["read"],
            )
            syft_perms.save(access_token_dir)

        # Create JWT token
        jwt_payload = JWTTokenPayload(
            router_name=router_name,
            router_author=router_author,
            delegate_email=delegate_email,
            control_type=control_type,
            created_at=datetime.now(),
        )

        # Create token file with random string
        jwt_token = jwt_payload.encode(settings.jwt_secret)

        token_file = access_token_dir / "delegation.jwt"
        token_file.write_text(jwt_token)

    def revoke_delegation(self, router_name: str) -> RevokeDelegationResponse:
        """Revoke delegation of a router.

        This function will revoke the delegation of a router.
        It will delete the delegate's email from the router's published metadata.
        It will delete delegate's email from router's metadata.
        """
        router = self.repository.get_router_by_name(router_name)

        if router.router_metadata.delegate_email is None:
            raise APIException(
                f"Router {router_name} is not delegated. Please delegate it first.",
                400,
            )

        delegate_email = router.router_metadata.delegate_email

        # Update router metadata
        router = self.repository.revoke_delegation(router_name)

        # Remove delegate's email from router published metadata
        project_metadata_path = (
            self.syftbox_client.my_datasite
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
            / router_name
            / "metadata.json"
        )

        # Check if published metadata exists
        if not project_metadata_path.exists():
            raise APIException(
                f"Router {router_name} is not published.",
                404,
            )

        # Remove delegate's email from router published metadata
        project_metadata = ProjectMetadata.load_from_file(project_metadata_path)
        project_metadata.delegate_email = None
        project_metadata.save_to_file(project_metadata_path)

        # Remove Token directory
        token_dir = (
            self.syftbox_client.my_datasite
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
            / router_name
            / "token"
        )
        if token_dir.exists():
            shutil.rmtree(token_dir)

        return RevokeDelegationResponse(
            router_name=router_name,
            delegate_email=delegate_email,
        )

    def _validate_delegate_access_token(
        self,
        access_token: str,
        router_name: str,
        delegate_email: EmailStr,
        control_type: DelegateControlType,
        router_author: str,
    ) -> bool:
        """Validate delegate access token.

        This function will validate the delegate access token.
        """
        # JWT Token decode
        jwt_payload = JWTTokenPayload.decode(
            access_token,
            settings.jwt_secret,
        )

        # Validate JWT payload
        return (
            jwt_payload.router_name == router_name
            and jwt_payload.router_author == router_author
            and jwt_payload.delegate_email == delegate_email
            and jwt_payload.control_type == control_type
        )

    def delegate_control_router(
        self, request: DelegateControlRequest
    ) -> DelegateControlResponse:
        """Delegate control of a router.

        This function will handle the control request from a delegate.
        It will return the updated router.

        Args:
            request: The control request from a delegate.

        Returns:
            The response to the delegate control request.
        """
        # Check if router exists
        router = self.repository.get_router_by_name(request.router_name)

        # Check if router exists
        if router is None:
            raise APIException(f"Router {request.router_name} not found", 404)

        # Check if router is delegated to the delegate
        if router.router_metadata.delegate_email != request.delegate_email:
            raise APIException(
                f"Router {request.router_name} is not delegated to {request.delegate_email}.",
                401,
            )

        # Validate access token
        valid_access_token = self._validate_delegate_access_token(
            request.delegate_access_token,
            router.name,
            request.delegate_email,
            request.control_type,
            router.author,
        )

        # Check if control type is valid
        if request.control_type not in DelegateControlType.all_types():
            raise APIException(
                f"Invalid control type: {request.control_type}",
                400,
            )

        if not valid_access_token:
            raise APIException(
                "Invalid access token. Please check the access token and try again.",
                401,
            )

        # Handle pricing update
        if request.control_type == DelegateControlType.UPDATE_PRICING:
            # Check if pricing updates are provided
            if request.control_data.pricing_updates is None:
                raise APIException(
                    "No pricing updates provided.",
                    400,
                )

            # Handle pricing update
            router = self._handle_delegate_pricing_update(
                router.name, request.control_data.pricing_updates
            )

        # Log audit
        self.repository.log_delegate_control_action(
            DelegateControlAuditCreate(
                router_name=router.name,
                delegate_email=request.delegate_email,
                control_type=request.control_type,
                control_data=request.control_data.model_dump(),
                reason=request.reason,
            )
        )

        # Return success response
        return DelegateControlResponse(
            success=True,
            router_name=router.name,
            message=f"Pricing updated successfully for router {router.name}.",
        )

    def get_delegate_access_token(
        self,
        router_name: str,
        router_author: str,
    ) -> str:
        """Get delegate access token.

        This function will get the delegate access token for a router.
        """
        token_file = (
            self.syftbox_client.datasites
            / router_author
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
            / router_name
            / "token"
            / "delegation.jwt"
        )

        if not token_file.exists():
            raise APIException(
                f"Delegate access token not found for router {router_name}.",
                404,
            )

        return token_file.read_text()

    def _handle_delegate_pricing_update(
        self, router_name: str, pricing_data: List[ServicePricingUpdate]
    ) -> Router:
        """Handle pricing update from delegate.

        This function will update the router's services pricing.
        It will update the router's published metadata with the new pricing.
        It will return the updated router.

        Args:
            router_name: The name of the router to update.
            pricing_data: The pricing data to update.

        Returns:
            The updated router.
        """

        router_update = RouterUpdate(
            services=[
                RouterService(
                    type=service.service_type,
                    pricing=service.new_pricing,
                    charge_type=service.new_charge_type,
                    enabled=True,
                )
                for service in pricing_data
            ],
        )

        router = self.repository.create_or_update_router(
            router_name=router_name,
            router_update=router_update,
        )

        # Update published metadata
        metadata_path = (
            self.syftbox_client.my_datasite
            / PUBLIC_ROUTER_DIR_NAME
            / ROUTER_DIR_NAME
            / router_name
            / "metadata.json"
        )

        metadata = ProjectMetadata.load_from_file(metadata_path)
        metadata.services = [
            ServiceOverview(
                type=service.type,
                pricing=service.pricing,
                charge_type=service.charge_type,
                enabled=service.enabled,
            )
            for service in router.services
        ]

        metadata.save_to_file(metadata_path)

        return router

    def get_delegate_control_audit_logs(self, router_name: str) -> DCALogsResponse:
        """Get delegate control audit logs.

        This function will get the audit logs for a router.
        """
        return DCALogsResponse(
            audit_logs=self.repository.get_delegate_control_audit_logs(router_name)
        )
