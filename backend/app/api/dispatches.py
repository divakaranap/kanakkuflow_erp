from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.dispatch import DispatchStatus
from backend.app.dependencies import get_current_user, require_roles
from backend.app.schemas.dispatch import (
    DispatchCreate,
    DispatchUpdate,
    DispatchResponse,
    OrderDispatchStatusResponse,
)
from backend.app.services import dispatch_service
from backend.app.services.pdf_service import generate_delivery_challan_pdf_buffer

router = APIRouter(prefix="/dispatches", tags=["Dispatch & Finished Goods"])


@router.get("/orders/{order_id}/status", response_model=OrderDispatchStatusResponse)
def get_order_dispatch_status(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inspect order fulfillment status, remaining balances, and finished goods availability."""
    return dispatch_service.get_order_dispatch_status(db, order_id)


@router.post("", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
def create_dispatch(
    payload: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER, UserRole.PRODUCTION])),
):
    """Create a new dispatch record in DRAFT status."""
    disp = dispatch_service.create_dispatch_draft(db, payload, current_user.id)
    resp = DispatchResponse.model_validate(disp)
    resp.customer_name = disp.customer.customer_name if disp.customer else None
    resp.order_number = disp.sales_order.order_number if disp.sales_order else None
    resp.invoice_number = disp.invoice.invoice_number if disp.invoice else None
    resp.creator_name = disp.creator.full_name if disp.creator else None
    for it, db_it in zip(resp.items, disp.items):
        it.product_name = db_it.product.product_name if db_it.product else None
        it.product_sku = db_it.product.sku if db_it.product else None
    return resp


@router.get("", response_model=dict)
def list_dispatches(
    customer_id: Optional[str] = Query(None),
    sales_order_id: Optional[str] = Query(None),
    status: Optional[DispatchStatus] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List dispatches with filtering and pagination."""
    items, total = dispatch_service.list_dispatches(db, customer_id, sales_order_id, status, page, limit)
    results = []
    for d in items:
        resp = DispatchResponse.model_validate(d)
        resp.customer_name = d.customer.customer_name if d.customer else None
        resp.order_number = d.sales_order.order_number if d.sales_order else None
        resp.invoice_number = d.invoice.invoice_number if d.invoice else None
        resp.creator_name = d.creator.full_name if d.creator else None
        for it, db_it in zip(resp.items, d.items):
            it.product_name = db_it.product.product_name if db_it.product else None
            it.product_sku = db_it.product.sku if db_it.product else None
        results.append(resp)

    return {
        "items": results,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{dispatch_id}", response_model=DispatchResponse)
def get_dispatch(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dispatch details by ID."""
    disp = dispatch_service.get_dispatch(db, dispatch_id)
    if not disp:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    resp = DispatchResponse.model_validate(disp)
    resp.customer_name = disp.customer.customer_name if disp.customer else None
    resp.order_number = disp.sales_order.order_number if disp.sales_order else None
    resp.invoice_number = disp.invoice.invoice_number if disp.invoice else None
    resp.creator_name = disp.creator.full_name if disp.creator else None
    for it, db_it in zip(resp.items, disp.items):
        it.product_name = db_it.product.product_name if db_it.product else None
        it.product_sku = db_it.product.sku if db_it.product else None
    return resp


@router.post("/{dispatch_id}/post", response_model=DispatchResponse)
def post_dispatch(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER, UserRole.PRODUCTION])),
):
    """
    Atomically post dispatch:
    - Deducts finished goods stock from inventory ledger (INVOICE_DISPATCH).
    - Updates fulfilled quantities on order lines.
    - Transitions dispatch to DISPATCHED.
    """
    disp = dispatch_service.post_dispatch(db, dispatch_id, current_user.id)
    resp = DispatchResponse.model_validate(disp)
    resp.customer_name = disp.customer.customer_name if disp.customer else None
    resp.order_number = disp.sales_order.order_number if disp.sales_order else None
    resp.invoice_number = disp.invoice.invoice_number if disp.invoice else None
    for it, db_it in zip(resp.items, disp.items):
        it.product_name = db_it.product.product_name if db_it.product else None
        it.product_sku = db_it.product.sku if db_it.product else None
    return resp


@router.post("/{dispatch_id}/cancel", response_model=DispatchResponse)
def cancel_dispatch(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Cancel a draft dispatch."""
    disp = dispatch_service.cancel_dispatch(db, dispatch_id, current_user.id)
    return disp


@router.get("/{dispatch_id}/challan")
def download_delivery_challan(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download delivery challan PDF."""
    disp = dispatch_service.get_dispatch(db, dispatch_id)
    if not disp:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    pdf_buffer = generate_delivery_challan_pdf_buffer(disp)
    filename = f"Challan_{disp.dispatch_number}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
