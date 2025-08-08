from fastapi import APIRouter, Depends
from fastapi import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from shared.exceptions import APIException

from .manager import RouterManager
from .schemas import (
    AvailableDelegatesResponse,
    CreateRouterRequest,
    CreateRouterResponse,
    DCALogsResponse,
    DelegateControlRequest,
    DelegateControlResponse,
    DelegateRouterRequest,
    DelegateRouterResponse,
    PublishRouterRequest,
    RevokeDelegationRequest,
    RevokeDelegationResponse,
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

    @router.post("/delegate/grant", response_model=DelegateRouterResponse)
    async def grant_delegate_access(
        request: DelegateRouterRequest,
        service: RouterManager = Depends(get_router_service),
    ):
        """Delegate a router to a delegate."""
        try:
            return service.grant_delegate_access(
                request.router_name, request.delegate_email
            )
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.post("/delegate/revoke", response_model=RevokeDelegationResponse)
    async def revoke_delegation(
        request: RevokeDelegationRequest,
        service: RouterManager = Depends(get_router_service),
    ):
        """Revoke delegation of a router."""
        try:
            return service.revoke_delegation(request.router_name)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/delegate/list", response_model=AvailableDelegatesResponse)
    async def list_delegates(service: RouterManager = Depends(get_router_service)):
        """List all delegates."""
        try:
            return service.get_available_delegates()
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.post("/opt-in-as-delegate", response_class=JSONResponse)
    async def opt_in_as_delegate(
        service: RouterManager = Depends(get_router_service),
    ):
        """Opt in as a delegate.

        This function will opt in the current user as a delegate.
        """
        try:
            is_success = service.make_user_a_delegate()
            return JSONResponse(status_code=200, content={"success": is_success})
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/delegate/logs", response_model=DCALogsResponse)
    async def get_delegate_control_audit_logs(
        router_name: str, service: RouterManager = Depends(get_router_service)
    ):
        """Get delegate control audit logs."""
        try:
            return service.get_delegate_control_audit_logs(router_name)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.post(
        "/delegate/control",
        response_model=DelegateControlResponse,
        tags=["syftbox"],
    )
    async def delegate_control(
        request: DelegateControlRequest,
        service: RouterManager = Depends(get_router_service),
    ):
        """Delegate control of a router."""
        try:
            return service.delegate_control_router(request)
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    @router.get("/delegate/access-token", response_class=JSONResponse)
    async def get_delegate_access_token(
        router_name: str,
        router_author: str,
        service: RouterManager = Depends(get_router_service),
    ):
        """Get delegate access token."""
        try:
            return JSONResponse(
                status_code=200,
                content={
                    "access_token": service.get_delegate_access_token(
                        router_name, router_author
                    )
                },
            )
        except APIException as e:
            raise FastAPIHTTPException(status_code=e.status_code, detail=e.message)

    return router
