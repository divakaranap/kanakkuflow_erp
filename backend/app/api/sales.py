from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.sales import SalesOrderStatus, InvoiceStatus
from backend.app.dependencies import get_current_user, require_roles
from backend.app.schemas.sales import (
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderResponse,
    SalesInvoiceCreate,
    SalesInvoiceResponse,
    InvoiceCancelRequest,
    ProductStockCheckResponse,
)
from backend.app.services import sales_service, dispatch_service
from backend.app.services.pdf_service import generate_invoice_pdf_buffer

router = APIRouter(prefix="/sales", tags=["Sales Orders & GST Invoicing"])


@router.get("/orders/{order_id}/dispatch-status")
def get_order_dispatch_status_route(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve fulfillment and stock availability status for order dispatch."""
    return dispatch_service.get_order_dispatch_status(db, order_id)


# -------------------------------------------------------------
# Stock Availability Helper
# -------------------------------------------------------------
@router.get("/check-stock", response_model=ProductStockCheckResponse)
def check_stock_availability(
    product_id: UUID = Query(...),
    quantity: Decimal = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check available finished goods stock for order entry without deducting."""
    return sales_service.check_product_stock_availability(db, product_id, quantity)


# -------------------------------------------------------------
# Sales Orders
# -------------------------------------------------------------
@router.post("/orders", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SALESMAN, UserRole.ADMIN, UserRole.OWNER])),
):
    """Create a new sales order in DRAFT status with GST calculations."""
    order = sales_service.create_sales_order(db, payload, current_user.id)
    return order


@router.get("/orders", response_model=dict)
def list_sales_orders(
    customer_id: Optional[UUID] = Query(None),
    status: Optional[SalesOrderStatus] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List sales orders with filtering and pagination."""
    items, total = sales_service.list_sales_orders(db, customer_id, status, page, limit)
    # Populate customer names for response
    results = []
    for o in items:
        resp = SalesOrderResponse.model_validate(o)
        resp.customer_name = o.customer.customer_name if o.customer else None
        resp.customer_code = o.customer.customer_code if o.customer else None
        resp.creator_name = o.creator.full_name if o.creator else None
        for it, db_it in zip(resp.items, o.items):
            it.product_name = db_it.product.product_name if db_it.product else None
            it.product_sku = db_it.product.sku if db_it.product else None
        results.append(resp)

    return {
        "items": results,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get sales order by ID with line items and GST breakdown."""
    order = sales_service.get_sales_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    resp = SalesOrderResponse.model_validate(order)
    resp.customer_name = order.customer.customer_name if order.customer else None
    resp.customer_code = order.customer.customer_code if order.customer else None
    resp.creator_name = order.creator.full_name if order.creator else None
    for it, db_it in zip(resp.items, order.items):
        it.product_name = db_it.product.product_name if db_it.product else None
        it.product_sku = db_it.product.sku if db_it.product else None
    return resp


@router.patch("/orders/{order_id}", response_model=SalesOrderResponse)
def update_sales_order(
    order_id: UUID,
    payload: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SALESMAN, UserRole.ADMIN, UserRole.OWNER])),
):
    """Update draft sales order lines or notes."""
    order = sales_service.update_sales_order(db, order_id, payload, current_user.id)
    return order


@router.post("/orders/{order_id}/submit", response_model=SalesOrderResponse)
def submit_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SALESMAN, UserRole.ADMIN, UserRole.OWNER])),
):
    """Submit a draft sales order for Admin verification."""
    order = sales_service.submit_sales_order(db, order_id, current_user.id)
    return order


@router.post("/orders/{order_id}/approve", response_model=SalesOrderResponse)
def approve_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Approve a submitted sales order (Admin/Owner authorization)."""
    order = sales_service.approve_sales_order(db, order_id, current_user.id)
    return order


@router.post("/orders/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Cancel a sales order."""
    order = sales_service.cancel_sales_order(db, order_id, current_user.id)
    return order


# -------------------------------------------------------------
# Sales Invoices
# -------------------------------------------------------------
@router.post("/invoices", response_model=SalesInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_sales_invoice(
    payload: SalesInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Create and post an immutable GST Tax Invoice for an approved sales order."""
    inv = sales_service.create_and_post_sales_invoice(
        db, payload.sales_order_id, payload.invoice_date, current_user.id
    )
    resp = SalesInvoiceResponse.model_validate(inv)
    resp.customer_name = inv.customer.customer_name if inv.customer else None
    resp.order_number = inv.sales_order.order_number if inv.sales_order else None
    resp.creator_name = inv.creator.full_name if inv.creator else None
    return resp


@router.get("/invoices", response_model=dict)
def list_sales_invoices(
    customer_id: Optional[UUID] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List sales invoices with filtering and pagination."""
    items, total = sales_service.list_sales_invoices(db, customer_id, status, page, limit)
    results = []
    for inv in items:
        resp = SalesInvoiceResponse.model_validate(inv)
        resp.customer_name = inv.customer.customer_name if inv.customer else None
        resp.order_number = inv.sales_order.order_number if inv.sales_order else None
        resp.creator_name = inv.creator.full_name if inv.creator else None
        results.append(resp)

    return {
        "items": results,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/invoices/{invoice_id}", response_model=SalesInvoiceResponse)
def get_sales_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get sales invoice details by ID."""
    inv = sales_service.get_sales_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Sales invoice not found")
    resp = SalesInvoiceResponse.model_validate(inv)
    resp.customer_name = inv.customer.customer_name if inv.customer else None
    resp.order_number = inv.sales_order.order_number if inv.sales_order else None
    resp.creator_name = inv.creator.full_name if inv.creator else None
    return resp


@router.post("/invoices/{invoice_id}/cancel", response_model=SalesInvoiceResponse)
def cancel_sales_invoice(
    invoice_id: UUID,
    payload: InvoiceCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Cancel a posted GST invoice with audit reason."""
    inv = sales_service.cancel_sales_invoice(db, invoice_id, payload.cancellation_reason, current_user.id)
    resp = SalesInvoiceResponse.model_validate(inv)
    resp.customer_name = inv.customer.customer_name if inv.customer else None
    resp.order_number = inv.sales_order.order_number if inv.sales_order else None
    return resp


@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a professional GST Tax Invoice PDF."""
    inv = sales_service.get_sales_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Sales invoice not found")

    pdf_buffer = generate_invoice_pdf_buffer(inv)
    filename = f"Invoice_{inv.invoice_number}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
