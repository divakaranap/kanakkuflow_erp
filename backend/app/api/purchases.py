from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_production
from backend.app.models.user import User
from backend.app.models.purchase import PurchaseStatus
from backend.app.schemas.purchase import PurchaseCreate, PurchaseOut
from backend.app.services import purchase_service

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.post("", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
def create_purchase(
    payload: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """Create a draft purchase order (Production / Admin / Owner)."""
    purchase = purchase_service.create_purchase(db=db, purchase_in=payload, user_id=current_user.id)
    return purchase_service.get_purchase_out(db, purchase)


@router.get("", response_model=Dict[str, Any])
def list_purchases(
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    status: Optional[PurchaseStatus] = Query(None, description="Filter by purchase status"),
    search: Optional[str] = Query(None, description="Search by PO number or invoice number"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List purchase orders with pagination and filtering."""
    items, total = purchase_service.list_purchases(
        db=db,
        supplier_id=supplier_id,
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


@router.get("/{purchase_id}", response_model=PurchaseOut)
def get_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve details of a specific purchase order."""
    return purchase_service.get_purchase(db=db, purchase_id=purchase_id)


@router.post("/{purchase_id}/post", response_model=PurchaseOut)
def post_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """Post purchase receipt: atomically updates inventory ledger and moving weighted average (Production / Admin / Owner)."""
    purchase = purchase_service.post_purchase(db=db, purchase_id=purchase_id, user_id=current_user.id)
    return purchase_service.get_purchase_out(db, purchase)
