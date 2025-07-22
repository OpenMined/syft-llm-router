from pathlib import Path
import hashlib
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from syft_core.config import SyftClientConfig
from fastsyftbox import FastSyftBox

from router.api import build_router_api
from router.manager import RouterManager
from router.repository import RouterRepository
from shared.database import Database
from accounting.api import build_accounting_api
from accounting.manager import AccountingManager
from accounting.schemas import AccountingConfig
from settings.app_settings import settings

# Initialize FastAPI app with SyftBox
syftbox_config = SyftClientConfig.load(settings.syftbox_config_path)

app = FastSyftBox(
    app_name=settings.app_name,
    syftbox_endpoint_tags=["syftbox"],
    include_syft_openapi=True,
    syftbox_config=syftbox_config,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database
def get_db_name() -> str:
    db_name = f"{app.syftbox_config.email}-{app.syftbox_config.data_dir.resolve()}"
    return hashlib.md5(db_name.encode()).hexdigest()


db_name = get_db_name()
db = Database(db_path=Path(__file__).parent.parent / "data" / f"{db_name}.db")
db.create_db_and_tables()


def init_router_manager() -> RouterManager:
    """Initialize the router manager."""
    router_repository = RouterRepository(db=db)
    router_manager = RouterManager(
        repository=router_repository,
        syftbox_config=syftbox_config,
        syftbox_client=app.syftbox_client,
        router_app_dir=app.syftbox_client.workspace.data_dir / "apps",
        template_dir=Path(__file__).parent / "generator",
    )
    return router_manager


def init_accounting_manager() -> AccountingManager:
    """Initialize the accounting manager."""

    accounting_config = AccountingConfig(
        email=settings.accounting_email,
        password=settings.accounting_password,
        url=settings.accounting_url,
    )
    accounting_manager = AccountingManager(
        syftbox_config=app.syftbox_config,
        accounting_config=accounting_config,
    )
    accounting_manager.get_or_create_user_account()
    return accounting_manager


# Include router API
app.include_router(build_router_api(init_router_manager()))
app.include_router(build_accounting_api(init_accounting_manager()))

# Mount static files for frontend
static_dir = Path(__file__).parent / "static"
assets_dir = static_dir / "assets"

# Create assets directory if it doesn't exist
assets_dir.mkdir(parents=True, exist_ok=True)

# Mount assets directory
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Mount static directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the frontend index.html for the root path"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # Fallback to simple HTML if frontend not built
    return HTMLResponse(
        content="<html><body><h1>Welcome to SyftRouter</h1>"
        + f"{app.get_debug_urls()}"
        + "</body></html>"
    )


@app.get("/username")
async def user_details():
    """Get current user details"""
    return {"username": app.syftbox_client.email}


@app.get("/sburl")
async def sburl():
    """Get SyftBox URL"""
    return {"url": str(app.syftbox_config.server_url)}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
