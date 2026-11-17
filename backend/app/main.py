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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables for development / test databases
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

# Versioned API routes
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(users_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "tagline": "From Order to Production. From Stock to Audit.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
