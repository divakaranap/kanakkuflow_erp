from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_admin_or_owner, require_production
from backend.app.models.user import User
from backend.app.models.inventory import (
    InventoryItemType,
    MovementType,
    AdjustmentStatus,
)
from backend.app.schemas.inventory import (
    OpeningStockCreate,
    StockMovementOut,
    StockSummaryItem,
    StockValuationItem,
    StockValuationSummary,
    StockReconciliationReport,
    AdjustmentCreate,
    AdjustmentOut,
)
from backend.app.services import inventory_service

router = APIRouter(tags=["Inventory & Stock Ledger"])


# 1. Opening Stock Initialization
@router.post("/inventory/opening-stock", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
def initialize_opening_stock(
    payload: OpeningStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner),
):
    """Initialize opening stock for an inventory item (Admin/Owner only)."""
    movement = inventory_service.initialize_opening_stock(
        db=db,
        item_type=payload.item_type,
        item_id=payload.item_id,
        quantity=payload.quantity,
        unit_cost_paise=payload.unit_cost_paise,
        user_id=current_user.id,
        notes=payload.notes,
        batch_id=payload.batch_id,
        reference_number=payload.reference_number,
    )
    meta = inventory_service.get_item_metadata(db, payload.item_type, payload.item_id)
    return StockMovementOut(
        id=movement.id,
        item_type=movement.item_type,
        item_id=movement.item_id,
        item_name=meta["name"],
        item_code=meta["code"],
        batch_id=movement.batch_id,
        movement_type=movement.movement_type,
        qty_delta=movement.qty_delta,
        unit_cost_paise=movement.unit_cost_paise,
        total_value_paise=movement.total_value_paise,
        source_type=movement.source_type,
        source_id=movement.source_id,
        reference_number=movement.reference_number,
        notes=movement.notes,
        created_by=movement.created_by,
        created_at=movement.created_at,
    )


# 2. Stock Summary
@router.get("/stock/summary", response_model=List[StockSummaryItem])
def get_stock_summary(
    item_type: Optional[InventoryItemType] = Query(None, description="Filter by RAW, PACKAGING, FG"),
    search: Optional[str] = Query(None, description="Search by item code or name"),
    low_stock_only: bool = Query(False, description="Filter items below reorder level"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve consolidated stock summary with current quantities, rates, and valuations."""
    return inventory_service.get_stock_summary(
        db=db,
        item_type=item_type,
        search=search,
        low_stock_only=low_stock_only,
    )


@router.get("/stock/summary/{item_type}/{item_id}", response_model=StockSummaryItem)
def get_item_stock_summary(
    item_type: InventoryItemType,
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve stock summary for a specific item."""
    items = inventory_service.get_stock_summary(db=db, item_type=item_type)
    for it in items:
        if it.item_id == item_id:
            return it
    raise HTTPException(status_code=404, detail="Item not found in stock summary")


# 3. Stock Movement Ledger
@router.get("/stock/ledger", response_model=Dict[str, Any])
def get_stock_ledger(
    item_type: Optional[InventoryItemType] = Query(None),
    item_id: Optional[str] = Query(None),
    movement_type: Optional[MovementType] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Query immutable stock ledger with comprehensive filters and pagination."""
    items, total = inventory_service.get_stock_ledger(
        db=db,
        item_type=item_type,
        item_id=item_id,
        movement_type=movement_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        limit=limit,
    )
    return {
        "items": [it.model_dump() for it in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


# 4. Inventory Valuation
@router.get("/stock/valuation", response_model=StockValuationSummary)
def get_stock_valuation(
    item_type: Optional[InventoryItemType] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Calculate total and categorized inventory valuation using moving weighted average."""
    return inventory_service.get_stock_valuation(db=db, item_type=item_type)


@router.get("/stock/valuation/{item_type}/{item_id}", response_model=StockValuationItem)
def get_item_stock_valuation(
    item_type: InventoryItemType,
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Calculate moving weighted average valuation for a single item."""
    summary = inventory_service.get_stock_valuation(db=db, item_type=item_type, item_id=item_id)
    if not summary.items:
        raise HTTPException(status_code=404, detail="Item valuation not found")
    return summary.items[0]


# 5. Stock Reconciliation
@router.get("/stock/reconciliation", response_model=StockReconciliationReport)
def get_stock_reconciliation(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """View inventory reconciliation comparing ledger SUM(qty_delta) against cached balances."""
    return inventory_service.reconcile_inventory(db=db)


@router.post("/stock/reconciliation/run", response_model=StockReconciliationReport)
def run_stock_reconciliation(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Force run reconciliation engine and synchronize cached inventory balances (Admin/Owner only)."""
    return inventory_service.reconcile_inventory(db=db)


# 6. Inventory Adjustments
@router.post("/inventory/adjustments", response_model=AdjustmentOut, status_code=status.HTTP_201_CREATED)
def create_inventory_adjustment(
    payload: AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_production),
):
    """Create a new draft inventory adjustment (Production / Admin / Owner)."""
    adj = inventory_service.create_adjustment(db=db, adj_in=payload, user_id=current_user.id)
    meta = inventory_service.get_item_metadata(db, adj.item_type, adj.item_id)
    return AdjustmentOut(
        id=adj.id,
        adjustment_number=adj.adjustment_number,
        item_type=adj.item_type,
        item_id=adj.item_id,
        item_name=meta["name"],
        item_code=meta["code"],
        adjustment_type=adj.adjustment_type,
        quantity=adj.quantity,
        reason=adj.reason,
        reference_number=adj.reference_number,
        status=adj.status,
        created_by=adj.created_by,
        approved_by=adj.approved_by,
        posted_at=adj.posted_at,
        created_at=adj.created_at,
        updated_at=adj.updated_at,
    )


@router.get("/inventory/adjustments", response_model=Dict[str, Any])
def list_inventory_adjustments(
    item_type: Optional[InventoryItemType] = Query(None),
    status: Optional[AdjustmentStatus] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List inventory adjustments with status and metadata."""
    items, total = inventory_service.list_adjustments(
        db=db,
        item_type=item_type,
        status=status,
        page=page,
        limit=limit,
    )
    return {
        "items": [it.model_dump() for it in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/inventory/adjustments/{adjustment_id}/post", response_model=AdjustmentOut)
def post_inventory_adjustment(
    adjustment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner),
):
    """Post an inventory adjustment, immutably applying the change to stock ledger (Admin/Owner only)."""
    adj = inventory_service.post_adjustment(db=db, adjustment_id=adjustment_id, user_id=current_user.id)
    meta = inventory_service.get_item_metadata(db, adj.item_type, adj.item_id)
    return AdjustmentOut(
        id=adj.id,
        adjustment_number=adj.adjustment_number,
        item_type=adj.item_type,
        item_id=adj.item_id,
        item_name=meta["name"],
        item_code=meta["code"],
        adjustment_type=adj.adjustment_type,
        quantity=adj.quantity,
        reason=adj.reason,
        reference_number=adj.reference_number,
        status=adj.status,
        created_by=adj.created_by,
        approved_by=adj.approved_by,
        posted_at=adj.posted_at,
        created_at=adj.created_at,
        updated_at=adj.updated_at,
    )
