from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from backend.app.models.customer import Customer
from backend.app.models.product import Product
from backend.app.models.inventory import (
    InventoryBalance,
    InventoryItemType,
    StockMovement,
    MovementType,
)
from backend.app.models.sales import (
    SalesOrder,
    SalesOrderItem,
    SalesInvoice,
    SalesOrderStatus,
)
from backend.app.models.dispatch import (
    Dispatch,
    DispatchItem,
    DispatchStatus,
)
from backend.app.schemas.dispatch import (
    DispatchCreate,
    DispatchUpdate,
    OrderDispatchStatusResponse,
    OrderItemDispatchStatus,
)


def generate_dispatch_number(db: Session) -> str:
    """Generate sequential, transaction-safe dispatch number (e.g. DSP-202611-0001)."""
    now = datetime.now()
    prefix = f"DSP-{now.strftime('%Y%m')}-"
    last = (
        db.query(Dispatch.dispatch_number)
        .filter(Dispatch.dispatch_number.like(f"{prefix}%"))
        .order_by(Dispatch.dispatch_number.desc())
        .first()
    )
    if not last:
        seq = 1
    else:
        try:
            seq = int(last[0].split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


def get_order_dispatch_status(db: Session, order_id: Any) -> OrderDispatchStatusResponse:
    """Analyze order fulfillment status, remaining quantities, and available FG stock."""
    order = db.query(SalesOrder).filter(SalesOrder.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")

    item_statuses = []
    overall_can_dispatch = True

    for it in order.items:
        prd = it.product
        ordered = Decimal(str(it.ordered_quantity))
        fulfilled = Decimal(str(it.fulfilled_quantity))
        pending = max(Decimal("0.0000"), ordered - fulfilled)

        # Check FG stock
        bal = (
            db.query(InventoryBalance)
            .filter(
                InventoryBalance.item_type == InventoryItemType.FG,
                InventoryBalance.item_id == str(it.product_id),
            )
            .first()
        )
        avail = bal.cached_qty if bal else Decimal("0.0000")
        has_sufficient = avail >= pending if pending > 0 else True

        if pending > 0 and not has_sufficient:
            overall_can_dispatch = False

        item_statuses.append(
            OrderItemDispatchStatus(
                sales_order_item_id=str(it.id),
                product_id=str(it.product_id),
                product_name=prd.product_name if prd else "Product",
                ordered_quantity=ordered,
                fulfilled_quantity=fulfilled,
                pending_quantity=pending,
                available_stock_quantity=avail,
                has_sufficient_stock=has_sufficient,
            )
        )

    return OrderDispatchStatusResponse(
        sales_order_id=str(order.id),
        order_number=order.order_number,
        customer_id=str(order.customer_id),
        customer_name=order.customer.customer_name if order.customer else "Customer",
        order_status=order.status.value,
        items=item_statuses,
        can_dispatch=overall_can_dispatch,
    )


def create_dispatch_draft(
    db: Session,
    data: DispatchCreate,
    current_user_id: int,
) -> Dispatch:
    """Create a new dispatch record in DRAFT status with stock validation."""
    order = db.query(SalesOrder).filter(SalesOrder.id == str(data.sales_order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status not in [SalesOrderStatus.APPROVED, SalesOrderStatus.PARTIALLY_FULFILLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot dispatch order in '{order.status.value}' status. Order must be APPROVED.",
        )

    disp_num = generate_dispatch_number(db)
    disp_date = data.dispatch_date or date.today()

    dispatch = Dispatch(
        dispatch_number=disp_num,
        sales_order_id=str(order.id),
        invoice_id=str(data.invoice_id) if data.invoice_id else None,
        customer_id=str(order.customer_id),
        dispatch_date=disp_date,
        status=DispatchStatus.DRAFT,
        transporter_name=data.transporter_name,
        vehicle_number=data.vehicle_number,
        tracking_reference=data.tracking_reference,
        notes=data.notes,
        created_by=current_user_id,
    )
    db.add(dispatch)
    db.flush()

    for it_in in data.items:
        so_item = db.query(SalesOrderItem).filter(SalesOrderItem.id == str(it_in.sales_order_item_id)).first()
        if not so_item:
            raise HTTPException(status_code=404, detail=f"Order item {it_in.sales_order_item_id} not found")

        qty_to_disp = Decimal(str(it_in.quantity_dispatched))
        pending_qty = Decimal(str(so_item.ordered_quantity)) - Decimal(str(so_item.fulfilled_quantity))

        if qty_to_disp > pending_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Requested dispatch quantity ({qty_to_disp}) exceeds pending order balance ({pending_qty})",
            )

        # Check available FG inventory
        bal = (
            db.query(InventoryBalance)
            .filter(
                InventoryBalance.item_type == InventoryItemType.FG,
                InventoryBalance.item_id == str(it_in.product_id),
            )
            .first()
        )
        avail = bal.cached_qty if bal else Decimal("0.0000")
        if qty_to_disp > avail:
            shortage = qty_to_disp - avail
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient finished goods stock for product. Available: {avail}, Requested: {qty_to_disp}, Shortage: {shortage}",
            )

        disp_item = DispatchItem(
            dispatch_id=str(dispatch.id),
            sales_order_item_id=str(so_item.id),
            product_id=str(it_in.product_id),
            quantity_dispatched=qty_to_disp,
            batch_reference=it_in.batch_reference,
            unit=so_item.product.base_unit if so_item.product else "packet",
        )
        db.add(disp_item)

    db.commit()
    db.refresh(dispatch)
    return dispatch


def post_dispatch(
    db: Session,
    dispatch_id: Any,
    current_user_id: int,
) -> Dispatch:
    """
    Post dispatch atomically:
    1. Re-validate available finished goods inventory.
    2. Deduct inventory via StockMovement ('INVOICE_DISPATCH').
    3. Update InventoryBalance cached_qty and total_value_paise.
    4. Increment fulfilled_quantity on SalesOrderItems.
    5. Update SalesOrder status (FULFILLED or PARTIALLY_FULFILLED).
    6. Transition Dispatch status to DISPATCHED.
    """
    dispatch = db.query(Dispatch).filter(Dispatch.id == str(dispatch_id)).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch record not found")
    if dispatch.status == DispatchStatus.DISPATCHED:
        raise HTTPException(status_code=400, detail="Dispatch is already posted")
    if dispatch.status == DispatchStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot post cancelled dispatch")

    order = dispatch.sales_order

    for item in dispatch.items:
        qty_num = Decimal(str(item.quantity_dispatched))

        # 1. Row-level check on inventory balance
        bal = (
            db.query(InventoryBalance)
            .filter(
                InventoryBalance.item_type == InventoryItemType.FG,
                InventoryBalance.item_id == str(item.product_id),
            )
            .with_for_update()
            .first()
        )
        avail = bal.cached_qty if bal else Decimal("0.0000")
        if qty_num > avail:
            shortage = qty_num - avail
            raise HTTPException(
                status_code=400,
                detail=f"Cannot post dispatch. Insufficient stock on hand for product. Available: {avail}, Shortage: {shortage}",
            )

        # 2. Derive unit valuation from moving weighted average
        if bal and bal.cached_qty > Decimal("0"):
            rate_paise = int(round(Decimal(bal.total_value_paise) / bal.cached_qty))
        else:
            rate_paise = 0
        total_val_deducted = int(round(Decimal(rate_paise) * qty_num))

        # 3. Create negative stock movement in ledger
        movement = StockMovement(
            item_type=InventoryItemType.FG,
            item_id=str(item.product_id),
            movement_type=MovementType.INVOICE_DISPATCH,
            qty_delta=-qty_num,
            unit_cost_paise=rate_paise,
            total_value_paise=total_val_deducted,
            source_type="DISPATCH",
            source_id=str(dispatch.id),
            reference_number=dispatch.dispatch_number,
            notes=f"Physical dispatch of {qty_num} pkts to {dispatch.customer.customer_name if dispatch.customer else 'Customer'}",
            created_by=current_user_id,
        )
        db.add(movement)

        # 4. Synchronize inventory balance
        bal.cached_qty -= qty_num
        bal.total_value_paise = max(0, bal.total_value_paise - total_val_deducted)

        # 5. Update sales order item fulfilled quantity
        so_item = item.sales_order_item
        so_item.fulfilled_quantity += qty_num

    # 6. Evaluate order fulfillment status
    all_fulfilled = True
    any_fulfilled = False
    for so_it in order.items:
        if so_it.fulfilled_quantity < so_it.ordered_quantity:
            all_fulfilled = False
        if so_it.fulfilled_quantity > Decimal("0"):
            any_fulfilled = True

    if all_fulfilled:
        order.status = SalesOrderStatus.FULFILLED
    elif any_fulfilled:
        order.status = SalesOrderStatus.PARTIALLY_FULFILLED

    # 7. Update dispatch status
    dispatch.status = DispatchStatus.DISPATCHED
    dispatch.dispatched_by = current_user_id
    dispatch.dispatched_at = datetime.now()

    db.commit()
    db.refresh(dispatch)
    return dispatch


def cancel_dispatch(
    db: Session,
    dispatch_id: Any,
    current_user_id: int,
) -> Dispatch:
    """Cancel a draft dispatch."""
    dispatch = db.query(Dispatch).filter(Dispatch.id == str(dispatch_id)).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch record not found")
    if dispatch.status == DispatchStatus.DISPATCHED:
        raise HTTPException(status_code=400, detail="Cannot cancel an already posted dispatch")

    dispatch.status = DispatchStatus.CANCELLED
    db.commit()
    db.refresh(dispatch)
    return dispatch


def get_dispatch(db: Session, dispatch_id: Any) -> Optional[Dispatch]:
    return db.query(Dispatch).filter(Dispatch.id == str(dispatch_id)).first()


def list_dispatches(
    db: Session,
    customer_id: Optional[Any] = None,
    sales_order_id: Optional[Any] = None,
    status: Optional[DispatchStatus] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[Dispatch], int]:
    q = db.query(Dispatch)
    if customer_id:
        q = q.filter(Dispatch.customer_id == str(customer_id))
    if sales_order_id:
        q = q.filter(Dispatch.sales_order_id == str(sales_order_id))
    if status:
        q = q.filter(Dispatch.status == status)
    total = q.count()
    items = q.order_by(Dispatch.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total
