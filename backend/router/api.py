from fastapi import APIRouter, Depends
from fastapi import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from shared.exceptions import APIException

from .manager import RouterManager
from .schemas import (
    CreateRouterRequest,
    CreateRouterResponse,
    PublishRouterRequest,
    RouterDetails,
    RouterList,
    RouterRunStatus,
)


def build_router_api(router_manager: RouterManager) -> APIRouter:
    """Create a router API router."""

    # Create router API router
    router = APIRouter(prefix="/router")

    # Create dependency function for router manager
    def get_router_service() -> RouterManager:
        return router_manager

    @router.post("/create", response_model=CreateRouterResponse)
    async def create_router(
        request: CreateRouterRequest,
        service: RouterManager = Depends(get_router_service),
    ):
        """Create a new router app."""
        try:
            return service.create_router(request)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/exists", response_model=bool)
    async def router_exists(
        name: str, service: RouterManager = Depends(get_router_service)
    ):
        """Check if a router with the given name exists."""
        return service.router_exists(name)

    @router.post("/publish")
    async def publish_router(
        request: PublishRouterRequest,
        service: RouterManager = Depends(get_router_service),
    ):
        """Publish a router app."""
        try:
            result = service.publish_router(request)
            return JSONResponse(status_code=200, content=result)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.put("/unpublish")
    async def unpublish_router(
        router_name: str, service: RouterManager = Depends(get_router_service)
    ):
        """Unpublish a router."""
        try:
            result = service.unpublish_router(router_name)
            return JSONResponse(status_code=200, content=result)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/list", response_model=RouterList)
    async def list_routers(service: RouterManager = Depends(get_router_service)):
        """List current datasite routers + all published routers from other datasites."""
        return service.list_routers()

    @router.delete("/delete")
    async def delete_router(
        router_name: str,
        published: bool,
        service: RouterManager = Depends(get_router_service),
    ):
        """Delete a router app."""
        try:
            result = service.delete_router(router_name, published)
            return JSONResponse(status_code=200, content=result)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/details", response_model=RouterDetails)
    async def router_details(
        router_name: str,
        author: str,
        published: bool,
        service: RouterManager = Depends(get_router_service),
    ):
        """Fetch the details of a router app."""
        try:
            return service.get_router_details(router_name, author, published)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/status", response_model=RouterRunStatus)
    async def router_status(
        router_name: str, service: RouterManager = Depends(get_router_service)
    ):
        """Get the status of the router."""
        try:
            return service.get_router_status(router_name)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    return router
