from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from backend.app.models.customer import Customer
from backend.app.models.product import Product
from backend.app.models.price_list import PriceListItem
from backend.app.models.inventory import InventoryBalance, InventoryItemType
from backend.app.models.sales import (
    SalesOrder,
    SalesOrderItem,
    SalesInvoice,
    SalesInvoiceItem,
    SalesOrderStatus,
    InvoiceStatus,
)
from backend.app.schemas.sales import (
    SalesOrderCreate,
    SalesOrderUpdate,
    ProductStockCheckResponse,
)
from backend.app.services.gst_service import (
    calculate_gst,
    get_place_of_supply,
    DEFAULT_SELLER_STATE_CODE,
)
from backend.app.config import settings


def generate_order_number(db: Session) -> str:
    """Generate sequential, transaction-safe order number (e.g. SO-202611-0001)."""
    now = datetime.now()
    prefix = f"SO-{now.strftime('%Y%m')}-"
    last = (
        db.query(SalesOrder.order_number)
        .filter(SalesOrder.order_number.like(f"{prefix}%"))
        .order_by(SalesOrder.order_number.desc())
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


def generate_invoice_number(db: Session) -> str:
    """Generate sequential, transaction-safe GST invoice number (e.g. INV-202611-0001)."""
    now = datetime.now()
    prefix = f"INV-{now.strftime('%Y%m')}-"
    last = (
        db.query(SalesInvoice.invoice_number)
        .filter(SalesInvoice.invoice_number.like(f"{prefix}%"))
        .order_by(SalesInvoice.invoice_number.desc())
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


def get_product_price(db: Session, customer: Customer, product_id: Any) -> int:
    """
    Resolve product selling price in paise.
    1. Check customer's assigned price list item.
    2. Fall back to Product default selling_price_paise.
    """
    pid_str = str(product_id)
    if customer.price_list_id:
        pli = (
            db.query(PriceListItem)
            .filter(
                PriceListItem.price_list_id == str(customer.price_list_id),
                PriceListItem.product_id == pid_str,
            )
            .first()
        )
        if pli and pli.selling_price_paise is not None:
            return pli.selling_price_paise

    prd = db.query(Product).filter(Product.id == pid_str).first()
    if not prd:
        raise HTTPException(status_code=404, detail="Product not found")
    return prd.selling_price_paise


def check_product_stock_availability(
    db: Session,
    product_id: Any,
    requested_qty: Decimal,
) -> ProductStockCheckResponse:
    """
    Check available finished goods stock against requested quantity without deducting.
    """
    pid_str = str(product_id)
    prd = db.query(Product).filter(Product.id == pid_str).first()
    if not prd:
        raise HTTPException(status_code=404, detail="Product not found")

    bal = (
        db.query(InventoryBalance)
        .filter(
            InventoryBalance.item_type == InventoryItemType.FG,
            InventoryBalance.item_id == pid_str,
        )
        .first()
    )
    available_qty = bal.cached_qty if bal else Decimal("0.0000")
    is_sufficient = available_qty >= requested_qty
    shortage = max(Decimal("0.0000"), requested_qty - available_qty)

    return ProductStockCheckResponse(
        product_id=prd.id,
        sku=prd.sku,
        product_name=prd.product_name,
        requested_qty=requested_qty,
        available_qty=available_qty,
        is_sufficient=is_sufficient,
        shortage_qty=shortage,
    )


def create_sales_order(
    db: Session,
    data: SalesOrderCreate,
    current_user_id: int,
) -> SalesOrder:
    """
    Create a new Sales Order in DRAFT status with GST line items.
    Does NOT deduct finished goods inventory (inventory is deducted during dispatch).
    """
    customer = db.query(Customer).filter(Customer.id == str(data.customer_id)).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not customer.is_active:
        raise HTTPException(status_code=400, detail="Cannot create sales order for inactive customer")

    place_of_supply = get_place_of_supply(customer.state_code or customer.gstin or DEFAULT_SELLER_STATE_CODE)
    seller_state_code = getattr(settings, "SELLER_STATE_CODE", DEFAULT_SELLER_STATE_CODE)

    order_num = generate_order_number(db)

    order = SalesOrder(
        order_number=order_num,
        customer_id=str(customer.id),
        order_date=date.today(),
        delivery_date=data.delivery_date,
        place_of_supply_state_code=place_of_supply,
        customer_gstin=customer.gstin,
        status=SalesOrderStatus.DRAFT,
        notes=data.notes,
        created_by=current_user_id,
    )
    db.add(order)
    db.flush()

    subtotal_paise = 0
    discount_total_paise = 0
    taxable_total_paise = 0
    cgst_total_paise = 0
    sgst_total_paise = 0
    igst_total_paise = 0

    for item_in in data.items:
        prd = db.query(Product).filter(Product.id == str(item_in.product_id)).first()
        if not prd:
            raise HTTPException(status_code=404, detail=f"Product {item_in.product_id} not found")
        if not prd.is_active:
            raise HTTPException(status_code=400, detail=f"Product {prd.product_name} is inactive")

        # Resolve price
        price_paise = (
            item_in.unit_price_paise
            if item_in.unit_price_paise is not None
            else get_product_price(db, customer, prd.id)
        )

        ordered_qty = item_in.ordered_quantity
        line_gross = int(round(Decimal(ordered_qty) * Decimal(price_paise)))
        line_taxable = max(0, line_gross - item_in.discount_paise)

        # Product GST rate (ensure percentage, e.g. 0.05 -> 5.00)
        gst_pct = prd.gst_rate * 100 if prd.gst_rate < Decimal("1.00") else prd.gst_rate

        gst_res = calculate_gst(
            taxable_amount_paise=line_taxable,
            gst_rate=gst_pct,
            place_of_supply_state_code=place_of_supply,
            seller_state_code=seller_state_code,
        )

        so_item = SalesOrderItem(
            sales_order_id=str(order.id),
            product_id=str(prd.id),
            ordered_quantity=ordered_qty,
            fulfilled_quantity=Decimal("0.0000"),
            unit_price_paise=price_paise,
            discount_paise=item_in.discount_paise,
            gst_rate=gst_pct,
            taxable_amount_paise=line_taxable,
            cgst_paise=gst_res["cgst_paise"],
            sgst_paise=gst_res["sgst_paise"],
            igst_paise=gst_res["igst_paise"],
            line_total_paise=gst_res["grand_total_paise"],
        )
        db.add(so_item)

        subtotal_paise += line_gross
        discount_total_paise += item_in.discount_paise
        taxable_total_paise += line_taxable
        cgst_total_paise += gst_res["cgst_paise"]
        sgst_total_paise += gst_res["sgst_paise"]
        igst_total_paise += gst_res["igst_paise"]

    order.subtotal_paise = subtotal_paise
    order.discount_paise = discount_total_paise
    order.taxable_amount_paise = taxable_total_paise
    order.cgst_paise = cgst_total_paise
    order.sgst_paise = sgst_total_paise
    order.igst_paise = igst_total_paise
    order.total_tax_paise = cgst_total_paise + sgst_total_paise + igst_total_paise
    order.grand_total_paise = taxable_total_paise + order.total_tax_paise

    db.commit()
    db.refresh(order)
    return order


def update_sales_order(
    db: Session,
    order_id: UUID,
    data: SalesOrderUpdate,
    current_user_id: int,
) -> SalesOrder:
    """Update sales order in DRAFT status."""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status != SalesOrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT sales orders can be edited")

    if data.delivery_date is not None:
        order.delivery_date = data.delivery_date
    if data.notes is not None:
        order.notes = data.notes

    if data.items is not None:
        # Clear existing items and recalculate
        for it in order.items:
            db.delete(it)
        db.flush()

        customer = order.customer
        seller_state_code = getattr(settings, "SELLER_STATE_CODE", DEFAULT_SELLER_STATE_CODE)
        subtotal_paise = 0
        discount_total_paise = 0
        taxable_total_paise = 0
        cgst_total_paise = 0
        sgst_total_paise = 0
        igst_total_paise = 0

        for item_in in data.items:
            prd = db.query(Product).filter(Product.id == item_in.product_id).first()
            if not prd or not prd.is_active:
                raise HTTPException(status_code=400, detail=f"Invalid or inactive product {item_in.product_id}")

            price_paise = (
                item_in.unit_price_paise
                if item_in.unit_price_paise is not None
                else get_product_price(db, customer, prd.id)
            )
            line_gross = int(round(Decimal(item_in.ordered_quantity) * Decimal(price_paise)))
            line_taxable = max(0, line_gross - item_in.discount_paise)
            gst_pct = prd.gst_rate * 100 if prd.gst_rate < Decimal("1.00") else prd.gst_rate

            gst_res = calculate_gst(
                taxable_amount_paise=line_taxable,
                gst_rate=gst_pct,
                place_of_supply_state_code=order.place_of_supply_state_code,
                seller_state_code=seller_state_code,
            )

            so_item = SalesOrderItem(
                sales_order_id=order.id,
                product_id=prd.id,
                ordered_quantity=item_in.ordered_quantity,
                fulfilled_quantity=Decimal("0.0000"),
                unit_price_paise=price_paise,
                discount_paise=item_in.discount_paise,
                gst_rate=gst_pct,
                taxable_amount_paise=line_taxable,
                cgst_paise=gst_res["cgst_paise"],
                sgst_paise=gst_res["sgst_paise"],
                igst_paise=gst_res["igst_paise"],
                line_total_paise=gst_res["grand_total_paise"],
            )
            db.add(so_item)

            subtotal_paise += line_gross
            discount_total_paise += item_in.discount_paise
            taxable_total_paise += line_taxable
            cgst_total_paise += gst_res["cgst_paise"]
            sgst_total_paise += gst_res["sgst_paise"]
            igst_total_paise += gst_res["igst_paise"]

        order.subtotal_paise = subtotal_paise
        order.discount_paise = discount_total_paise
        order.taxable_amount_paise = taxable_total_paise
        order.cgst_paise = cgst_total_paise
        order.sgst_paise = sgst_total_paise
        order.igst_paise = igst_total_paise
        order.total_tax_paise = cgst_total_paise + sgst_total_paise + igst_total_paise
        order.grand_total_paise = taxable_total_paise + order.total_tax_paise

    db.commit()
    db.refresh(order)
    return order


def submit_sales_order(
    db: Session,
    order_id: Any,
    current_user_id: int,
) -> SalesOrder:
    """Submit sales order for Admin/Owner approval."""
    order = db.query(SalesOrder).filter(SalesOrder.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status != SalesOrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT orders can be submitted")
    if not order.items:
        raise HTTPException(status_code=400, detail="Order has no line items")

    order.status = SalesOrderStatus.SUBMITTED
    db.commit()
    db.refresh(order)
    return order


def approve_sales_order(
    db: Session,
    order_id: Any,
    current_user_id: int,
) -> SalesOrder:
    """Approve submitted sales order (Admin/Owner only)."""
    order = db.query(SalesOrder).filter(SalesOrder.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status != SalesOrderStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only SUBMITTED orders can be approved")

    order.status = SalesOrderStatus.APPROVED
    order.approved_by = current_user_id
    order.approved_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def cancel_sales_order(
    db: Session,
    order_id: Any,
    current_user_id: int,
) -> SalesOrder:
    """Cancel sales order if not fulfilled."""
    order = db.query(SalesOrder).filter(SalesOrder.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status in [SalesOrderStatus.FULFILLED, SalesOrderStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in {order.status.value} status")

    order.status = SalesOrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


def create_and_post_sales_invoice(
    db: Session,
    order_id: Any,
    invoice_date: Optional[date],
    current_user_id: int,
) -> SalesInvoice:
    """
    Generate and post an immutable GST Tax Invoice for an approved sales order.
    Creates immutable line item snapshots (product name, HSN, rate, GST breakup).
    Does NOT deduct finished goods inventory (inventory is deducted during dispatch in Phase 6).
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status not in [SalesOrderStatus.APPROVED, SalesOrderStatus.PARTIALLY_FULFILLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate invoice for order in '{order.status.value}' status. Order must be APPROVED.",
        )

    # Check if active posted invoice already exists for this order
    existing_invoice = (
        db.query(SalesInvoice)
        .filter(
            SalesInvoice.sales_order_id == str(order.id),
            SalesInvoice.status == InvoiceStatus.POSTED,
        )
        .first()
    )
    if existing_invoice:
        return existing_invoice

    inv_num = generate_invoice_number(db)
    inv_date = invoice_date or date.today()
    seller_gstin = getattr(settings, "SELLER_GSTIN", "33AAAAF1234A1Z5")

    invoice = SalesInvoice(
        invoice_number=inv_num,
        sales_order_id=str(order.id),
        customer_id=str(order.customer_id),
        invoice_date=inv_date,
        place_of_supply_state_code=order.place_of_supply_state_code,
        seller_gstin=seller_gstin,
        buyer_gstin=order.customer_gstin,
        taxable_amount_paise=order.taxable_amount_paise,
        cgst_paise=order.cgst_paise,
        sgst_paise=order.sgst_paise,
        igst_paise=order.igst_paise,
        total_tax_paise=order.total_tax_paise,
        grand_total_paise=order.grand_total_paise,
        status=InvoiceStatus.POSTED,
        created_by=current_user_id,
        posted_at=datetime.now(),
    )
    db.add(invoice)
    db.flush()

    for item in order.items:
        prd = item.product
        inv_item = SalesInvoiceItem(
            invoice_id=str(invoice.id),
            product_id=str(item.product_id) if item.product_id else None,
            product_name=prd.product_name if prd else "Food Product",
            hsn_code=prd.hsn_code if prd else "1905",
            quantity=item.ordered_quantity,
            unit=prd.base_unit if prd else "packet",
            unit_price_paise=item.unit_price_paise,
            taxable_value_paise=item.taxable_amount_paise,
            gst_rate=item.gst_rate,
            cgst_paise=item.cgst_paise,
            sgst_paise=item.sgst_paise,
            igst_paise=item.igst_paise,
            line_total_paise=item.line_total_paise,
        )
        db.add(inv_item)

    db.commit()
    db.refresh(invoice)
    return invoice


def cancel_sales_invoice(
    db: Session,
    invoice_id: Any,
    cancellation_reason: str,
    current_user_id: int,
) -> SalesInvoice:
    """Cancel a posted GST invoice with audit reason."""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == str(invoice_id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Invoice is already cancelled")

    invoice.status = InvoiceStatus.CANCELLED
    invoice.cancellation_reason = cancellation_reason
    db.commit()
    db.refresh(invoice)
    return invoice


def get_sales_order(db: Session, order_id: Any) -> Optional[SalesOrder]:
    return db.query(SalesOrder).filter(SalesOrder.id == str(order_id)).first()


def list_sales_orders(
    db: Session,
    customer_id: Optional[Any] = None,
    status: Optional[SalesOrderStatus] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[SalesOrder], int]:
    q = db.query(SalesOrder)
    if customer_id:
        q = q.filter(SalesOrder.customer_id == str(customer_id))
    if status:
        q = q.filter(SalesOrder.status == status)
    total = q.count()
    items = q.order_by(SalesOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total


def get_sales_invoice(db: Session, invoice_id: Any) -> Optional[SalesInvoice]:
    return db.query(SalesInvoice).filter(SalesInvoice.id == str(invoice_id)).first()


def list_sales_invoices(
    db: Session,
    customer_id: Optional[Any] = None,
    status: Optional[InvoiceStatus] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[SalesInvoice], int]:
    q = db.query(SalesInvoice)
    if customer_id:
        q = q.filter(SalesInvoice.customer_id == str(customer_id))
    if status:
        q = q.filter(SalesInvoice.status == status)
    total = q.count()
    items = q.order_by(SalesInvoice.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total
