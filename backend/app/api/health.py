import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from backend.app.database import engine
from backend.app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Lightweight health endpoint.
    Returns 200 OK without requiring database connectivity, ensuring instant
    cold-start checks and load balancer/platform liveness verification.
    """
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@router.get("/health/ready")
def readiness_check():
    """
    Readiness endpoint verifying actual database connectivity.
    Returns 200 OK when database is accessible, or 503 Service Unavailable
    when unreachable, without leaking internal credentials, hostnames, or exceptions.
    """
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": now_str,
        }
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "timestamp": now_str,
            },
        )
