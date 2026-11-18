from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database import get_db
from backend.app.dependencies import require_roles
from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer
from backend.app.models.product import Product
from backend.app.models.sales import SalesOrder
from backend.app.schemas.sales import SalesOrderCreate
from backend.app.schemas.sync import (
    SyncReferenceDataResponse,
    SyncCustomerItem,
    SyncProductItem,
    SyncOrdersRequest,
    SyncOrdersResponse,
    SyncedOrderItem,
    FailedOrderItem,
)
from backend.app.services.sales_service import create_sales_order

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/reference-data", response_model=SyncReferenceDataResponse)
def get_sync_reference_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN])),
):
    """
    Download active master data (customers and products) for mobile offline caching.
    """
    customers = (
        db.query(Customer)
        .filter(Customer.is_active == True)
        .order_by(Customer.customer_name)
        .all()
    )
    products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(Product.product_name)
        .all()
    )

    customer_items = [
        SyncCustomerItem(
            id=UUID(str(c.id)),
            customer_code=c.customer_code,
            customer_name=c.customer_name,
            phone=c.phone,
            gstin=c.gstin,
            state_code=c.state_code,
            credit_limit_paise=c.credit_limit_paise,
            is_active=c.is_active,
        )
        for c in customers
    ]

    product_items = [
        SyncProductItem(
            id=UUID(str(p.id)),
            sku=p.sku,
            product_name=p.product_name,
            category=p.category.value if hasattr(p.category, "value") else str(p.category),
            base_unit=p.base_unit,
            selling_price_paise=p.selling_price_paise,
            gst_rate=p.gst_rate,
            hsn_code=p.hsn_code,
            is_active=p.is_active,
        )
        for p in products
    ]

    return SyncReferenceDataResponse(
        timestamp=datetime.now(),
        customers=customer_items,
        products=product_items,
    )


@router.post("/orders", response_model=SyncOrdersResponse)
def sync_offline_orders(
    payload: SyncOrdersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN])),
):
    """
    Synchronize queued offline orders with server-side validation and idempotency protection.
    Duplicate submissions with the same client_order_uuid will not create duplicate orders.
    """
    synced_results: List[SyncedOrderItem] = []
    failed_results: List[FailedOrderItem] = []

    for item in payload.orders:
        client_ref_marker = f"[ClientRef: {item.client_order_uuid}]"

        # Check idempotency: does an order with this client UUID already exist?
        existing_order = (
            db.query(SalesOrder)
            .filter(SalesOrder.notes.like(f"%{client_ref_marker}%"))
            .first()
        )

        if existing_order:
            synced_results.append(
                SyncedOrderItem(
                    client_order_uuid=item.client_order_uuid,
                    sales_order_id=UUID(str(existing_order.id)),
                    order_number=existing_order.order_number,
                    grand_total_paise=existing_order.grand_total_paise,
                    status=existing_order.status.value if hasattr(existing_order.status, "value") else str(existing_order.status),
                )
            )
            continue

        try:
            # Prepare notes with client idempotency reference
            merged_notes = f"{item.notes or ''}\n{client_ref_marker}".strip()

            order_create_data = SalesOrderCreate(
                customer_id=item.customer_id,
                delivery_date=item.delivery_date,
                notes=merged_notes,
                items=item.items,
            )

            created_order = create_sales_order(
                db=db,
                data=order_create_data,
                current_user_id=current_user.id,
            )
            db.commit()

            synced_results.append(
                SyncedOrderItem(
                    client_order_uuid=item.client_order_uuid,
                    sales_order_id=UUID(str(created_order.id)),
                    order_number=created_order.order_number,
                    grand_total_paise=created_order.grand_total_paise,
                    status=created_order.status.value if hasattr(created_order.status, "value") else str(created_order.status),
                )
            )
        except HTTPException as he:
            db.rollback()
            failed_results.append(
                FailedOrderItem(
                    client_order_uuid=item.client_order_uuid,
                    error=str(he.detail),
                )
            )
        except Exception as e:
            db.rollback()
            failed_results.append(
                FailedOrderItem(
                    client_order_uuid=item.client_order_uuid,
                    error=str(e),
                )
            )

    return SyncOrdersResponse(
        synced=synced_results,
        failed=failed_results,
    )
