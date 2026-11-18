import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# ---------------------------------------------------------------------------
# Path setup: Ensure both repository root and backend directory are in sys.path
# so that imports like `from backend.app...` work seamlessly when executed
# from repository root, inside backend/, or within Vercel's serverless runtime.
# ---------------------------------------------------------------------------
_backend_dir = Path(__file__).resolve().parent.parent  # .../backend
_repo_root = _backend_dir.parent  # .../
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import engine
from backend.app.models.base import Base
import backend.app.models  # ensure all models are registered

from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.users import router as users_router
from backend.app.api.customers import router as customers_router
from backend.app.api.suppliers import router as suppliers_router
from backend.app.api.products import router as products_router
from backend.app.api.raw_materials import router as raw_materials_router
from backend.app.api.packaging import router as packaging_router
from backend.app.api.price_lists import router as price_lists_router
from backend.app.api.units import router as units_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.purchases import router as purchases_router
from backend.app.api.boms import router as boms_router
from backend.app.api.production import router as production_router
from backend.app.api.sales import router as sales_router
from backend.app.api.dispatches import router as dispatches_router
from backend.app.api.payments import router as payments_router
from backend.app.api.accounting import router as accounting_router
from backend.app.api.reports import router as reports_router
from backend.app.api.sync import router as sync_router
from backend.app.api.search import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables only for local development when not running in production, pytest, or Vercel.
    # Production deployments use safe, idempotent Alembic migrations.
    is_prod = (
        os.environ.get("VERCEL") == "1"
        or os.environ.get("ENVIRONMENT", "").lower() == "production"
        or getattr(settings, "ENVIRONMENT", "").lower() == "production"
    )
    if not is_prod and "pytest" not in sys.modules and not os.environ.get("PYTEST_CURRENT_TEST"):
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            print(f"[Lifespan Notice] Auto-create tables skipped or failed: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Integrated Order-to-Audit Management System for Small Food Manufacturers (NIT Trichy)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router Definitions Bundle
# Every router is registered at:
# 1. Root level (e.g. /health, /customers, /auth/login) for direct access & test suites
# 2. /api prefix (e.g. /api/health, /api/customers, /api/auth/login) for Vercel multi-service routing
# 3. /api/v1 prefix (e.g. /api/v1/health) for versioned API endpoints
# ---------------------------------------------------------------------------
api_routers = [
    (health_router, ""),
    (auth_router, "/auth"),
    (users_router, ""),
    (customers_router, ""),
    (suppliers_router, ""),
    (products_router, ""),
    (raw_materials_router, ""),
    (packaging_router, ""),
    (price_lists_router, ""),
    (units_router, ""),
    (inventory_router, ""),
    (purchases_router, ""),
    (boms_router, ""),
    (production_router, ""),
    (sales_router, ""),
    (dispatches_router, ""),
    (payments_router, ""),
    (accounting_router, ""),
    (reports_router, ""),
    (sync_router, ""),
    (search_router, ""),
]

# 1. Register at root level
for r, pfx in api_routers:
    if pfx:
        app.include_router(r, prefix=pfx)
    else:
        app.include_router(r)

# 2. Register under /api prefix (for Vercel rewrites & same-origin frontend requests)
api_router = APIRouter(prefix="/api")
for r, pfx in api_routers:
    if pfx:
        api_router.include_router(r, prefix=pfx)
    else:
        api_router.include_router(r)

@api_router.get("", include_in_schema=False)
@api_router.get("/", include_in_schema=False)
def api_root():
    return {
        "system": settings.PROJECT_NAME,
        "tagline": "From Order to Production. From Stock to Audit.",
        "status": "online",
        "docs": "/api/docs",
        "health": "/api/health",
        "version": "1.0.0",
    }

app.include_router(api_router)

# 3. Register under /api/v1 prefix (Versioned routes)
api_v1_router = APIRouter(prefix=settings.API_V1_STR)
for r, pfx in api_routers:
    if pfx:
        api_v1_router.include_router(r, prefix=pfx)
    else:
        api_v1_router.include_router(r)

app.include_router(api_v1_router)

# ---------------------------------------------------------------------------
# Vercel Documentation Compatibility (/api/docs and /api/openapi.json)
# ---------------------------------------------------------------------------
@app.get("/api/docs", include_in_schema=False)
async def api_swagger_ui():
    """Swagger UI documentation compatible with /api prefix in Vercel multi-service routing."""
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/api/openapi.json", include_in_schema=False)
async def api_openapi():
    """OpenAPI JSON schema compatible with /api prefix in Vercel multi-service routing."""
    return JSONResponse(content=app.openapi())

@app.get("/api/redoc", include_in_schema=False)
async def api_redoc():
    """ReDoc documentation compatible with /api prefix in Vercel multi-service routing."""
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
    )

# Root-level status
@app.get("/", include_in_schema=False)
def root():
    return {
        "system": settings.PROJECT_NAME,
        "tagline": "From Order to Production. From Stock to Audit.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api_docs": "/api/docs",
        "api_health": "/api/health",
    }
