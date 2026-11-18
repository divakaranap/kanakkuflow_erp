import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables for development when not running under pytest
    if "pytest" not in sys.modules and not os.environ.get("PYTEST_CURRENT_TEST"):
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            print(f"[Lifespan Warning] Could not automatically create tables: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Integrated Order-to-Audit Management System for Small Food Manufacturers (NIT Trichy)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level endpoints for spec compliance
app.include_router(health_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(customers_router)
app.include_router(suppliers_router)
app.include_router(products_router)
app.include_router(raw_materials_router)
app.include_router(packaging_router)
app.include_router(price_lists_router)
app.include_router(units_router)
app.include_router(inventory_router)
app.include_router(purchases_router)
app.include_router(boms_router)
app.include_router(production_router)
app.include_router(sales_router)
app.include_router(sales_router, prefix="/api")
app.include_router(dispatches_router)
app.include_router(dispatches_router, prefix="/api")
app.include_router(payments_router)
app.include_router(payments_router, prefix="/api")

# Versioned API routes (/api/v1/...)
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(suppliers_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(raw_materials_router, prefix=settings.API_V1_STR)
app.include_router(packaging_router, prefix=settings.API_V1_STR)
app.include_router(price_lists_router, prefix=settings.API_V1_STR)
app.include_router(units_router, prefix=settings.API_V1_STR)
app.include_router(inventory_router, prefix=settings.API_V1_STR)
app.include_router(purchases_router, prefix=settings.API_V1_STR)
app.include_router(boms_router, prefix=settings.API_V1_STR)
app.include_router(production_router, prefix=settings.API_V1_STR)
app.include_router(sales_router, prefix=settings.API_V1_STR)
app.include_router(dispatches_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "tagline": "From Order to Production. From Stock to Audit.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
