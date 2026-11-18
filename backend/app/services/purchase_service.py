from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.purchase import Purchase, PurchaseLine, PurchaseStatus, PurchaseItemType
from backend.app.models.supplier import Supplier
from backend.app.models.raw_material import RawMaterial
from backend.app.models.packaging import PackagingItem
from backend.app.models.inventory import InventoryItemType, MovementType
from backend.app.schemas.purchase import (
    PurchaseCreate,
    PurchaseUpdate,
    PurchaseLineCreate,
    PurchaseOut,
    PurchaseLineOut,
)
from backend.app.services.unit_conversion_service import normalize_quantity
from backend.app.services.inventory_service import create_stock_movement, get_item_metadata


def _resolve_item_base_unit(db: Session, item_type: PurchaseItemType, item_id: str) -> Tuple[str, str, str]:
    """Returns (item_code, item_name, base_unit)."""
    if item_type == PurchaseItemType.RAW:
        rm = db.execute(select(RawMaterial).where(RawMaterial.id == item_id)).scalar_one_or_none()
        if not rm:
            raise HTTPException(status_code=404, detail=f"Raw material {item_id} not found")
        return rm.material_code, rm.material_name, rm.base_unit
    elif item_type == PurchaseItemType.PACKAGING:
        pkg = db.execute(select(PackagingItem).where(PackagingItem.id == item_id)).scalar_one_or_none()
        if not pkg:
            raise HTTPException(status_code=404, detail=f"Packaging item {item_id} not found")
        return pkg.packaging_code, pkg.packaging_name, pkg.base_unit
    else:
        raise HTTPException(status_code=400, detail=f"Invalid purchase item type {item_type}")


def create_purchase(db: Session, purchase_in: PurchaseCreate, user_id: int) -> Purchase:
    """Create a new purchase order in DRAFT status with computed tax and normalized quantities."""
    # Verify supplier
    supplier = db.execute(select(Supplier).where(Supplier.id == purchase_in.supplier_id)).scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier {purchase_in.supplier_id} not found")

    # Generate unique purchase number PO-YYYYMMDD-XXXX
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    count_today = db.execute(
        select(func.count(Purchase.id)).where(Purchase.purchase_number.like(f"PO-{today_str}-%"))
    ).scalar_one()
    purchase_number = f"PO-{today_str}-{(count_today + 1):04d}"

    subtotal_paise = 0
    tax_paise = 0
    total_paise = 0

    purchase_lines: List[PurchaseLine] = []

    for line_in in purchase_in.lines:
        code, name, base_unit = _resolve_item_base_unit(db, line_in.item_type, line_in.item_id)

        # Normalize quantity to base unit (kg, litre, piece)
        qty = Decimal(str(line_in.quantity))
        norm_qty = normalize_quantity(qty, line_in.unit, base_unit)

        # Line financial calculations
        taxable_val = int(round(Decimal(line_in.unit_rate_paise) * qty))
        tax_val = int(round(Decimal(taxable_val) * Decimal(str(line_in.tax_rate))))
        line_total = taxable_val + tax_val

        subtotal_paise += taxable_val
        tax_paise += tax_val
        total_paise += line_total

        line = PurchaseLine(
            item_type=line_in.item_type,
            item_id=line_in.item_id,
            quantity=qty,
            unit=line_in.unit,
            normalized_quantity=norm_qty,
            unit_rate_paise=line_in.unit_rate_paise,
            taxable_value_paise=taxable_val,
            tax_rate=line_in.tax_rate,
            tax_paise=tax_val,
            line_total_paise=line_total,
            batch_number=line_in.batch_number,
            manufacturing_date=line_in.manufacturing_date,
            expiry_date=line_in.expiry_date,
        )
        purchase_lines.append(line)

    purchase = Purchase(
        purchase_number=purchase_number,
        supplier_id=purchase_in.supplier_id,
        supplier_invoice_number=purchase_in.supplier_invoice_number,
        purchase_date=purchase_in.purchase_date or datetime.now(timezone.utc),
        status=PurchaseStatus.DRAFT,
        subtotal_paise=subtotal_paise,
        tax_paise=tax_paise,
        total_paise=total_paise,
        notes=purchase_in.notes,
        created_by=user_id,
        lines=purchase_lines,
    )

    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def post_purchase(db: Session, purchase_id: str, user_id: int) -> Purchase:
    """Post purchase receipt: atomically update inventory ledger and moving weighted average."""
    purchase = db.execute(select(Purchase).where(Purchase.id == purchase_id)).scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    if purchase.status != PurchaseStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Cannot post purchase with status {purchase.status.value}")

    # Process all lines atomically
    for line in purchase.lines:
        inv_item_type = InventoryItemType.RAW if line.item_type == PurchaseItemType.RAW else InventoryItemType.PACKAGING
        norm_qty = Decimal(str(line.normalized_quantity))

        # Base unit rate in paise (taxable value / normalized quantity)
        if norm_qty > 0:
            rate_per_base_unit = int(round(Decimal(line.taxable_value_paise) / norm_qty))
        else:
            rate_per_base_unit = line.unit_rate_paise

        create_stock_movement(
            db=db,
            item_type=inv_item_type,
            item_id=line.item_id,
            movement_type=MovementType.PURCHASE_RECEIPT,
            qty_delta=norm_qty,
            unit_cost_paise=rate_per_base_unit,
            total_value_paise=line.taxable_value_paise,
            source_type="PURCHASE",
            source_id=purchase.id,
            reference_number=purchase.supplier_invoice_number,
            notes=f"Purchase {purchase.purchase_number} - Invoice {purchase.supplier_invoice_number}",
            user_id=user_id,
            batch_id=line.batch_number,
        )

    purchase.status = PurchaseStatus.POSTED
    purchase.posted_by = user_id
    purchase.posted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(purchase)
    return purchase


def get_purchase_out(db: Session, purchase: Purchase) -> PurchaseOut:
    """Enrich purchase object into PurchaseOut response with item codes and names."""
    supplier_name = purchase.supplier.supplier_name if purchase.supplier else "Unknown Supplier"

    lines_out: List[PurchaseLineOut] = []
    for l in purchase.lines:
        try:
            code, name, _ = _resolve_item_base_unit(db, l.item_type, l.item_id)
        except Exception:
            code, name = "UNKNOWN", "Unknown Item"

        lines_out.append(
            PurchaseLineOut(
                id=l.id,
                purchase_id=l.purchase_id,
                item_type=l.item_type,
                item_id=l.item_id,
                item_name=name,
                item_code=code,
                quantity=Decimal(str(l.quantity)),
                unit=l.unit,
                normalized_quantity=Decimal(str(l.normalized_quantity)),
                unit_rate_paise=l.unit_rate_paise,
                taxable_value_paise=l.taxable_value_paise,
                tax_rate=Decimal(str(l.tax_rate)),
                tax_paise=l.tax_paise,
                line_total_paise=l.line_total_paise,
                batch_number=l.batch_number,
                manufacturing_date=l.manufacturing_date,
                expiry_date=l.expiry_date,
            )
        )

    return PurchaseOut(
        id=purchase.id,
        purchase_number=purchase.purchase_number,
        supplier_id=purchase.supplier_id,
        supplier_name=supplier_name,
        supplier_invoice_number=purchase.supplier_invoice_number,
        purchase_date=purchase.purchase_date,
        status=purchase.status,
        subtotal_paise=purchase.subtotal_paise,
        tax_paise=purchase.tax_paise,
        total_paise=purchase.total_paise,
        notes=purchase.notes,
        created_by=purchase.created_by,
        posted_by=purchase.posted_by,
        posted_at=purchase.posted_at,
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
        lines=lines_out,
    )


def get_purchase(db: Session, purchase_id: str) -> PurchaseOut:
    """Retrieve single purchase by ID."""
    p = db.execute(select(Purchase).where(Purchase.id == purchase_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return get_purchase_out(db, p)


def list_purchases(
    db: Session,
    supplier_id: Optional[str] = None,
    status: Optional[PurchaseStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[PurchaseOut], int]:
    """Retrieve paginated purchases."""
    conditions = []
    if supplier_id:
        conditions.append(Purchase.supplier_id == supplier_id)
    if status:
        conditions.append(Purchase.status == status)
    if search:
        conditions.append(
            or_(
                Purchase.purchase_number.ilike(f"%{search}%"),
                Purchase.supplier_invoice_number.ilike(f"%{search}%"),
            )
        )

    query = select(Purchase)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count(Purchase.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = db.execute(count_query).scalar_one()

    offset = (page - 1) * limit
    purchases = db.execute(
        query.order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return [get_purchase_out(db, p) for p in purchases], total
