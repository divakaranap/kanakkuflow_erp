from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_production, require_admin_or_owner
from backend.app.models.user import User
from backend.app.models.production import ProductionRunStatus, VarianceStatus
from backend.app.schemas.production import (
    ProductionRunCreate,
    ProductionRunUpdate,
    ProductionRunOut,
    ProductionVarianceReport,
    ProductionCostingReport,
)
from backend.app.services import production_service, variance_service, costing_service

router = APIRouter(tags=["Production Engine"])


@router.post("/production-runs", response_model=ProductionRunOut, status_code=status.HTTP_201_CREATED)
def create_production_run(
    payload: ProductionRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """Create a draft production run (Production / Admin / Owner)."""
    run = production_service.create_production_run(db=db, run_in=payload, user_id=current_user.id)
    return production_service._enrich_production_run_out(db, run)


@router.get("/production-runs", response_model=Dict[str, Any])
def list_production_runs(
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    status: Optional[ProductionRunStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by run number or batch number"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List production runs with pagination and filters."""
    items, total = production_service.list_production_runs(
        db=db,
        product_id=product_id,
        status=status,
        search=search,
        page=page,
        limit=limit,
    )
    return {
        "items": [it.model_dump() for it in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/production-runs/{run_id}", response_model=ProductionRunOut)
def get_production_run(
    run_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve full details of a specific production run."""
    return production_service.get_production_run(db=db, run_id=run_id)


@router.patch("/production-runs/{run_id}", response_model=ProductionRunOut)
def update_production_run(
    run_id: str,
    payload: ProductionRunUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """Update quantities, materials, or overheads of a draft production run."""
    run = production_service.update_production_run(db=db, run_id=run_id, run_up=payload, user_id=current_user.id)
    return production_service._enrich_production_run_out(db, run)


@router.post("/production-runs/{run_id}/post", response_model=ProductionRunOut)
def post_production_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """
    Post production run:
    Atomically updates inventory ledger:
    - Decreases Raw Materials (PRODUCTION_ISSUE)
    - Decreases Packaging (PRODUCTION_ISSUE and PRODUCTION_SCRAP)
    - Increases Finished Goods (PRODUCTION_OUTPUT)
    - Sets final moving weighted-average unit costing
    """
    run = production_service.post_production_run(db=db, run_id=run_id, user_id=current_user.id)
    return production_service._enrich_production_run_out(db, run)


@router.get("/production-runs/{run_id}/variance", response_model=ProductionVarianceReport)
def get_production_run_variance(
    run_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Calculate material consumption and yield variance with tolerance alerts."""
    run = db.query(production_service.ProductionRun).filter(production_service.ProductionRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return variance_service.analyze_production_run_variance(run)


@router.get("/production-runs/{run_id}/costing", response_model=ProductionCostingReport)
def get_production_run_costing(
    run_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Calculate production run cost breakdown, cost per packet, and gross margin."""
    run = db.query(production_service.ProductionRun).filter(production_service.ProductionRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return costing_service.calculate_production_run_costing(db, run)


@router.get("/production/summary", response_model=Dict[str, Any])
def get_production_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve production KPI dashboard metrics."""
    return production_service.get_production_summary(db)


@router.get("/production/variance-alerts", response_model=Dict[str, Any])
def get_production_variance_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List production runs that exceeded variance tolerance thresholds."""
    items, total = production_service.list_production_runs(
        db=db,
        status=ProductionRunStatus.POSTED,
        page=page,
        limit=limit,
    )
    alert_items = [it for it in items if it.variance_status != VarianceStatus.NORMAL]
    return {
        "items": [it.model_dump() for it in alert_items],
        "total": len(alert_items),
        "page": page,
        "limit": limit,
    }
