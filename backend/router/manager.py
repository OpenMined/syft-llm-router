from pathlib import Path
from .repository import RouterRepository
from .models import RouterServiceType
from .schemas import (
    CreateRouterRequest,
    CreateRouterResponse,
    PublishRouterRequest,
    RouterList,
    RouterOverview,
    ServiceOverview,
    RouterDetails,
    RouterMetadataResponse,
    RouterRunStatus,
    RouterServiceStatus,
    RouterUpdate,
    RouterMetadata,
    RouterService,
    RouterCreate,
    PricingChargeType,
)
from generator.service import ProjectConfig, SimplifiedProjectGenerator
from generator.common.config import StateFile
from .publish import publish_project, unpublish_project
import json
import shutil
from .exceptions import HTTPException
from syft_core.config import SyftClientConfig
from syft_core import Client as SyftClient


class RouterManager:
    def __init__(
        self,
        repository: RouterRepository,
        syftbox_config: SyftClientConfig,
        syftbox_client: SyftClient,
        router_app_dir: Path,
        template_dir: Path,
    ):
        self.repository = repository
        self.syftbox_config = syftbox_config
        self.syftbox_client = syftbox_client
        self.router_app_dir = router_app_dir
        self.template_dir = template_dir

    def create_router(self, request: CreateRouterRequest) -> CreateRouterResponse:
        """Create a new router app"""
        author = self.get_current_user()

        config = ProjectConfig(
            project_name=request.name.strip(),
            router_type=request.router_type.value,
            enable_chat=RouterServiceType.CHAT in request.services,
            enable_search=RouterServiceType.SEARCH in request.services,
            syftbox_config=self.syftbox_config,
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
            raise HTTPException(f"Router {request.router_name} not found", 404)

        if router.published:
            raise HTTPException(f"Router {request.router_name} already published", 400)

        router_dir = self.router_app_dir / request.router_name
        if not router_dir.exists():
            raise HTTPException(
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
            raise HTTPException(
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
            raise HTTPException(f"Failed to update router {request.router_name}", 500)

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
            raise HTTPException(
                f"Router {router_name} not found or not owned by {self.get_current_user()}",
                404,
            )

        if not router.published:
            raise HTTPException(f"Router {router_name} is not published", 400)

        try:
            unpublish_project(router_name, self.syftbox_config.path)

            updated_router = self.repository.set_published_status(router_name, False)
            if updated_router is None:
                raise HTTPException(f"Failed to update router {router_name}", 500)
        except Exception as e:
            raise HTTPException(f"Error unpublishing router {router_name}: {e}", 500)

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
            routers_dir = datasite / "public" / "routers"

            # Skip if routers directory does not exist
            if not routers_dir.exists():
                continue

            # Iterate through all the routers in the datasite
            for router_dir in routers_dir.iterdir():
                metadata_path = Path(router_dir) / "metadata.json"
                if not metadata_path.exists():
                    continue

                # Load metadata
                metadata = json.loads(metadata_path.read_text())

                all_routers.append(
                    RouterOverview(
                        name=metadata["project_name"],
                        published=True,
                        author=metadata["author"],
                        summary=metadata["summary"],
                        services=[
                            ServiceOverview(
                                type=service["type"],
                                pricing=service["pricing"],
                                charge_type=service["charge_type"],
                                enabled=service["enabled"],
                            )
                            for service in metadata["services"]
                        ],
                    )
                )

        return RouterList(routers=all_routers)

    def delete_router(self, router_name: str, published: bool) -> dict:
        """Delete a router app"""
        router = self.repository.get_router_by_name(router_name)
        if router is None:
            raise HTTPException(f"Router {router_name} not found", 404)

        if router.published:
            public_metadata_path = (
                self.syftbox_client.my_datasite
                / "public"
                / "routers"
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
            raise HTTPException(f"Failed to delete router {router_name}", 500)

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
                raise HTTPException(f"Router {router_name} not found", 404)

            if router.router_metadata:
                metadata = RouterMetadataResponse(
                    summary=router.router_metadata.summary,
                    description=router.router_metadata.description,
                    tags=router.router_metadata.tags,
                    code_hash=router.router_metadata.code_hash,
                    author=router.author,
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
                / "public"
                / "routers"
                / router_name
            )
            if not router_dir.exists():
                raise HTTPException(f"Router {router_name} not found", 404)

            metadata_path = router_dir / "metadata.json"

            # Load metadata if it exists
            if metadata_path.exists():
                metadata_json = json.loads(metadata_path.read_text())

                metadata = RouterMetadataResponse(
                    summary=metadata_json["summary"],
                    description=metadata_json["description"],
                    tags=metadata_json["tags"],
                    code_hash=metadata_json["code_hash"],
                    author=metadata_json["author"],
                )

                endpoints = metadata_json["documented_endpoints"]

                services = [
                    ServiceOverview(
                        type=RouterServiceType(service["type"]),
                        pricing=service["pricing"],
                        charge_type=service["charge_type"],
                        enabled=service["enabled"],
                    )
                    for service in metadata_json["services"]
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
            raise HTTPException(f"Router {router_name} not found", 404)

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
