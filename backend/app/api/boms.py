from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_production, require_admin_or_owner
from backend.app.models.user import User
from backend.app.models.bom import BOMStatus
from backend.app.schemas.bom import (
    BOMCreate,
    BOMUpdate,
    BOMOut,
    BOMScalingResponse,
)
from backend.app.services import bom_service

router = APIRouter(prefix="/boms", tags=["Bill of Materials (BOM)"])


@router.post("", response_model=BOMOut, status_code=status.HTTP_201_CREATED)
def create_bom(
    payload: BOMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """Create a new BOM version (Production / Admin / Owner)."""
    bom = bom_service.create_bom(db=db, bom_in=payload, user_id=current_user.id)
    return bom_service._enrich_bom_out(db, bom)


@router.get("", response_model=Dict[str, Any])
def list_boms(
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    status: Optional[BOMStatus] = Query(None, description="Filter by BOM status"),
    search: Optional[str] = Query(None, description="Search by BOM code or description"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all BOMs with version and item details."""
    items, total = bom_service.list_boms(
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


@router.get("/active/{product_id}", response_model=BOMOut)
def get_active_bom(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve current active BOM for a finished product."""
    bom = bom_service.get_active_bom(db=db, product_id=product_id)
    return bom_service._enrich_bom_out(db, bom)


@router.get("/{bom_id}", response_model=BOMOut)
def get_bom(
    bom_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve details of a specific BOM."""
    bom = db.query(bom_service.BOM).filter(bom_service.BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    return bom_service._enrich_bom_out(db, bom)


@router.post("/{bom_id}/activate", response_model=BOMOut)
def activate_bom(
    bom_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Activate a BOM version and archive any older active version (Admin / Owner only)."""
    bom = bom_service.activate_bom(db=db, bom_id=bom_id)
    return bom_service._enrich_bom_out(db, bom)


@router.post("/{bom_id}/archive", response_model=BOMOut)
def archive_bom(
    bom_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Archive a BOM version (Admin / Owner only)."""
    bom = bom_service.archive_bom(db=db, bom_id=bom_id)
    return bom_service._enrich_bom_out(db, bom)


@router.get("/{bom_id}/scale", response_model=BOMScalingResponse)
def scale_bom(
    bom_id: str,
    batches: Decimal = Query(Decimal("1.00"), gt=0, description="Number of production batches"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Calculate expected output and planned material requirements with inventory sufficiency check."""
    return bom_service.scale_bom(db=db, bom_id=bom_id, number_of_batches=batches)
