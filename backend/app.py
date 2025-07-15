from pathlib import Path
import shutil
import json

from pydantic import EmailStr
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException

from syft_core.config import SyftClientConfig
from fastsyftbox import FastSyftBox
from fastapi.responses import JSONResponse
from publish import publish_project, unpublish_project
from router_generator.generate import ProjectConfig, SimplifiedProjectGenerator
from constant import RouterServiceType
from db import (
    SessionDep,
    Router,
    RouterService,
    RouterMetadata,
    create_db_and_tables,
)
from serializer import (
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
)

from sqlmodel import select

app_name = "SyftRouter"

app = FastSyftBox(
    app_name=app_name,
    syftbox_endpoint_tags=[
        "syftbox"
    ],  # endpoints with this tag are also available via Syft RPC
    include_syft_openapi=True,  # Create OpenAPI endpoints for syft-rpc routes
    syftbox_config=SyftClientConfig.load(
        "/home/shubham/.syftbox/config.alice.dev.json"
    ),
)

ROUTER_APP_DIR = app.syftbox_client.workspace.data_dir / "apps"

# Mount static files for frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def root():
    # Serve the frontend index.html for the root path
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # Fallback to simple HTML if frontend not built
    return HTMLResponse(
        content=f"<html><body><h1>Welcome to {app_name}</h1>"
        + f"{app.get_debug_urls()}"
        + "</body></html>"
    )


# Router APIs


@app.api_route(
    path="/router/create",
    methods=["POST"],
)
async def create_router(
    request: CreateRouterRequest, session: SessionDep
) -> CreateRouterResponse:
    """Create a new router app

    This API will create a new router app in the `apps` directory.
    The router app is unpublished by default.
    The router details are saved to the database.

    Args:
        request (CreateRouterRequest): The request body containing the router details
        session (SessionDep): The database session

    Returns:
        CreateRouterResponse: The response containing the router name, output directory, and router type
    """

    config = ProjectConfig(
        project_name=request.name.strip(),
        router_type=request.router_type.value,
        enable_chat=RouterServiceType.CHAT in request.services,
        enable_search=RouterServiceType.SEARCH in request.services,
        syftbox_config=app.syftbox_client.config,
    )

    template_dir = Path(__file__).parent / "router_generator"

    # TODO: It can be refactored to use the `router_generator` package directly
    generator = SimplifiedProjectGenerator(template_dir=template_dir)

    output_dir = ROUTER_APP_DIR / config.project_name

    generator.generate_project(config, output_dir=output_dir)

    # Create router services
    router_services = []
    for service_type in RouterServiceType.all_types():
        enabled = RouterServiceType(service_type) in request.services
        router_services.append(RouterService(type=service_type, enabled=enabled))

    # Save router information to database
    router = Router(
        name=config.project_name,
        router_type=request.router_type,
        services=router_services,
        published=False,
        author=app.syftbox_client.email,
    )

    session.add(router)
    session.commit()

    return CreateRouterResponse(
        router_name=config.project_name,
        output_dir=output_dir,
        router_type=request.router_type,
    )


@app.api_route(
    path="/router/exists",
    methods=["GET"],
)
async def router_exists(name: str, session: SessionDep) -> bool:
    """Check if a router with the given name exists.

    The router name is unique. If the router exists, it will return True.

    Args:
        name (str): The name of the router to check
        session (SessionDep): The database session

    Returns:
        bool: True if the router exists, False otherwise
    """
    router = session.exec(select(Router).where(Router.name == name)).first()
    return router is not None


@app.api_route(
    path="/router/publish",
    methods=["POST"],
)
async def publish_router(
    request: PublishRouterRequest, session: SessionDep
) -> JSONResponse:
    """

    This API will publish a router app.
    - It fetches the unpublished router information from the database to create a metadata.json file.
    - This metadata.json is saved to the `public` directory of the datasite.
    - It also updates the router information in the database.
    - The router services are updated with the pricing information.
    - The router is marked as published.

    Published router cannot be re-published.

    Args:
        request (PublishRouterRequest): The request body containing the router details
        session (SessionDep): The database session

    Returns:
        JSONResponse: The response containing the message and the published path
    """

    router = session.exec(
        select(Router).where(Router.name == request.router_name)
    ).first()

    if router is None:
        return JSONResponse(
            status_code=404,
            content={"message": f"Router {request.router_name} not found"},
        )

    if router.published:
        return JSONResponse(
            status_code=400,
            content={"message": f"Router {request.router_name} already published"},
        )

    router_dir = ROUTER_APP_DIR / request.router_name

    if not router_dir.exists():
        return JSONResponse(
            status_code=404,
            content={
                "message": f"Router {request.router_name} not found in apps directory"
            },
        )

    try:
        metadata, published_path = publish_project(
            project_name=request.router_name,
            project_folder_path=router_dir,
            description=request.description,
            summary=request.summary,
            tags=request.tags,
            services=request.services,
            client_config_path=app.syftbox_client.config.path,
        )
    except Exception as e:
        print("Error", e)
        return JSONResponse(
            status_code=500,
            content={"message": f"Error publishing router {request.router_name}. {e}"},
        )

    # Save metadata to database
    if router.router_metadata is None:
        router_metadata = RouterMetadata(
            summary=request.summary,
            description=request.description,
            tags=request.tags,
            code_hash=metadata.code_hash,
            router_id=router.id,
        )
        router.router_metadata = router_metadata
    else:
        router.router_metadata.summary = request.summary
        router.router_metadata.description = request.description
        router.router_metadata.tags = request.tags
        router.router_metadata.code_hash = metadata.code_hash

    # Update existing services with pricing
    for service in request.services:
        for router_service in router.services:
            if router_service.type == service.type:
                router_service.pricing = service.pricing
                router_service.charge_type = service.charge_type
                router_service.enabled = service.enabled
                break

    router.published = True

    session.add(router)
    session.commit()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Router published successfully.",
            "published_path": str(published_path),
        },
    )


@app.api_route(
    path="/router/unpublish",
    methods=["POST"],
)
async def unpublish_router(router_name: str, session: SessionDep) -> JSONResponse:
    """Unpublish a router."""

    current_user = app.syftbox_client.email

    router = session.exec(
        select(Router).where(Router.name == router_name, Router.author == current_user)
    ).first()

    if router is None:
        return JSONResponse(
            status_code=404,
            content={
                "message": f"Router {router_name} not found or not owned by {current_user}"
            },
        )

    if not router.published:
        return JSONResponse(
            status_code=400,
            content={"message": f"Router {router_name} is not published"},
        )

    try:
        unpublish_project(router_name, app.syftbox_client.config.path)
        # Delete the router from the database
        router.published = False
        session.add(router)
        session.commit()
    except Exception as e:
        print("Error", e)
        return JSONResponse(
            status_code=500,
            content={"message": f"Error unpublishing router {router_name}. {e}"},
        )

    return JSONResponse(
        status_code=200,
        content={"message": "Router unpublished successfully."},
    )


@app.api_route(
    path="/router/list",
    methods=["GET"],
)
async def list_routers(session: SessionDep) -> RouterList:
    """List current datasite routers + all published routers from other datasites.

    The metadata of the owner's routers are fetched from the database.
    The metadata of the published routers are fetched from the `public` directory of the datasite.

    Args:
        session (SessionDep): The database session

    Returns:
        RouterList: The list of routers
    """

    # Fetch my routers from the database
    routers = session.exec(select(Router)).all()

    all_routers = []

    for router in routers:
        # Handle case where router_metadata might be None
        author = router.author

        all_routers.append(
            RouterOverview(
                name=router.name,
                published=router.published,
                summary=(
                    router.router_metadata.summary if router.router_metadata else ""
                ),
                author=author,
                services=[
                    ServiceOverview(
                        type=RouterServiceType(service.type.value),
                        pricing=service.pricing,
                        charge_type=service.charge_type,
                        enabled=service.enabled,
                    )
                    for service in router.services
                ],
            )
        )

    # Fetch published routers from other datasites from the `public/metadata.json` directory
    # Loop through all the datasites and fetch the metadata.json file
    for datasite in app.syftbox_client.datasites.iterdir():
        if datasite.name == app.syftbox_client.email:
            continue

        metadata_path = datasite / "public" / "routers" / "metadata.json"
        if metadata_path.exists():
            metadata = json.load(metadata_path.read_text())
            all_routers.append(
                RouterOverview(
                    name=metadata["name"],
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


@app.api_route(
    path="/router/delete",
    methods=["POST"],
)
async def delete_router(
    router_name: str, published: bool, session: SessionDep
) -> JSONResponse:
    """Delete a router app.

    This API will delete a router app.
    Only datasite belonging to the current user can be deleted.

    Args:
        router_name (str): The name of the router to delete
        published (bool): Whether the router is published
        session (SessionDep): The database session

    Returns:
        JSONResponse: The response containing the message
    """

    router = session.exec(select(Router).where(Router.name == router_name)).first()

    if router is None:
        return JSONResponse(
            status_code=404,
            content={"message": f"Router {router_name} not found"},
        )

    if router.published:
        public_metadata_path = (
            app.syftbox_client.my_datasite
            / "public"
            / "routers"
            / router_name
            / "metadata.json"
        )
        if public_metadata_path.exists():
            public_metadata_path.unlink()
    else:
        router_dir = ROUTER_APP_DIR / router_name
        if router_dir.exists():
            shutil.rmtree(router_dir)

    session.delete(router)
    session.commit()

    return JSONResponse(
        status_code=200, content={"message": "Router deleted successfully."}
    )


@app.api_route(
    path="/router/details",
    methods=["GET"],
)
async def router_details(
    router_name: str, author: EmailStr, published: bool, session: SessionDep
) -> RouterDetails:
    """Fetch the details of a router app.

    This API will fetch the details of a router app.

    If the router belongs to the current user, the details are fetched from the database.
    If the router is published, the details are fetched from the `public` directory of the datasite.

    Args:
        router_name (str): The name of the router to fetch
        published (bool): Whether the router is published
        session (SessionDep): The database session

    Returns:
        RouterDetails: The details of the router
    """

    metadata = None
    services = []
    endpoints = {}

    if author == app.syftbox_client.email:
        # Fetch router information from the database
        router = session.exec(
            select(Router).where(
                Router.name == router_name,
                Router.published == published,
            )
        ).first()

        if router is None:
            return JSONResponse(
                status_code=404,
                content={"message": f"Router {router_name} not found"},
            )

        if router.router_metadata:
            # Create a services object from the services

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
                        type=RouterServiceType(service.type.value),
                        pricing=service.pricing,
                        charge_type=service.charge_type,
                        enabled=service.enabled,
                    )
                )
        published = router.published

        endpoints_dir = ROUTER_APP_DIR / router_name / f"{router_name}.openapi.json"
        if endpoints_dir.exists():
            endpoints = json.loads(endpoints_dir.read_text())

    else:
        # Fetch router information from the `public` directory of the datasite
        router_dir = (
            app.syftbox_client.datasites / author / "public" / "routers" / router_name
        )

        print(router_dir)
        print(router_dir.exists())

        if not router_dir.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "message": f"Router {router_name} not found. Path: {router_dir}"
                },
            )

        metadata_path = router_dir / "metadata.json"

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

    return RouterDetails(
        name=router_name,
        published=published,
        metadata=metadata,
        services=services,
        endpoints=endpoints,
    )


@app.api_route(
    path="/username",
    methods=["GET"],
)
async def user_details() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"username": app.syftbox_client.email},
    )


@app.api_route(
    path="/router/status",
    methods=["GET"],
)
async def router_status(router_name: str, session: SessionDep) -> RouterRunStatus:
    """Get the status of the router.

    This API will get the status of the router.
    """

    router = session.exec(select(Router).where(Router.name == router_name)).first()

    if router is None:
        return JSONResponse(
            status_code=404,
            content={"message": f"Router {router_name} not found"},
        )

    from router_generator.common.config import StateFile

    state_file_path = ROUTER_APP_DIR / router_name / "state.json"

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


@app.api_route(
    path="/sburl",
    methods=["GET"],
)
async def sburl() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"url": str(app.syftbox_config.server_url)},
    )


# Catch-all route for SPA routing - serve index.html for any frontend route
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Don't interfere with API routes
    if full_path.startswith(("router/", "username", "sburl", "docs", "openapi")):
        raise HTTPException(status_code=404, detail="Not found")

    # Serve index.html for frontend routes
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Not found")


create_db_and_tables()
