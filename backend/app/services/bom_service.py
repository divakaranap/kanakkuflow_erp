import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.bom import BOM, BOMItem, BOMStatus
from backend.app.models.product import Product
from backend.app.models.raw_material import RawMaterial
from backend.app.models.packaging import PackagingItem
from backend.app.models.inventory import InventoryItemType
from backend.app.schemas.bom import (
    BOMCreate,
    BOMUpdate,
    BOMOut,
    BOMItemOut,
    BOMPlannedItem,
    BOMScalingResponse,
)
from backend.app.services.inventory_service import get_stock_balance, get_item_metadata
from backend.app.services.unit_conversion_service import validate_unit


def _enrich_bom_out(db: Session, bom: BOM) -> BOMOut:
    """Enrich BOM with product and item metadata."""
    product = db.execute(select(Product).where(Product.id == bom.product_id)).scalar_one_or_none()
    product_name = product.product_name if product else "Unknown Product"
    product_sku = product.sku if product else "UNKNOWN"

    items_out: List[BOMItemOut] = []
    for item in bom.items:
        try:
            meta = get_item_metadata(db, item.item_type, item.item_id)
            code, name = meta["code"], meta["name"]
        except Exception:
            code, name = "UNKNOWN", "Unknown Item"

        items_out.append(
            BOMItemOut(
                id=item.id,
                bom_id=item.bom_id,
                item_type=item.item_type,
                item_id=item.item_id,
                item_name=name,
                item_code=code,
                quantity_per_batch=Decimal(str(item.quantity_per_batch)),
                unit=item.unit,
                created_at=item.created_at,
            )
        )

    return BOMOut(
        id=bom.id,
        bom_code=bom.bom_code,
        product_id=bom.product_id,
        product_name=product_name,
        product_sku=product_sku,
        version=bom.version,
        batch_yield_packets=Decimal(str(bom.batch_yield_packets)),
        tolerance_pct=Decimal(str(bom.tolerance_pct)),
        description=bom.description,
        status=bom.status,
        effective_from=bom.effective_from,
        effective_until=bom.effective_until,
        created_by=bom.created_by,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
        items=items_out,
    )


def create_bom_snapshot(db: Session, bom: BOM) -> str:
    """Create an immutable JSON snapshot of the BOM recipe at time of production."""
    items_data = []
    for it in bom.items:
        try:
            meta = get_item_metadata(db, it.item_type, it.item_id)
            code, name = meta["code"], meta["name"]
        except Exception:
            code, name = "UNKNOWN", "Unknown Item"

        items_data.append({
            "item_type": it.item_type.value,
            "item_id": it.item_id,
            "item_code": code,
            "item_name": name,
            "quantity_per_batch": str(it.quantity_per_batch),
            "unit": it.unit,
        })

    snapshot = {
        "bom_id": bom.id,
        "bom_code": bom.bom_code,
        "version": bom.version,
        "product_id": bom.product_id,
        "batch_yield_packets": str(bom.batch_yield_packets),
        "tolerance_pct": str(bom.tolerance_pct),
        "items": items_data,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(snapshot)


def get_active_bom(db: Session, product_id: str, production_date: Optional[datetime] = None) -> BOM:
    """Fetch the active BOM version for a product on a specific date."""
    query = select(BOM).where(
        and_(
            BOM.product_id == product_id,
            BOM.status == BOMStatus.ACTIVE,
        )
    )
    if production_date:
        query = query.where(
            and_(
                BOM.effective_from <= production_date,
                or_(BOM.effective_until == None, BOM.effective_until >= production_date),
            )
        )

    bom = db.execute(query.order_by(BOM.version.desc())).scalars().first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active BOM found for product {product_id}",
        )
    return bom


def create_bom(db: Session, bom_in: BOMCreate, user_id: int) -> BOM:
    """Create a new BOM version."""
    product = db.execute(select(Product).where(Product.id == bom_in.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {bom_in.product_id} not found")

    # Determine next version number
    max_version = db.execute(
        select(func.coalesce(func.max(BOM.version), 0)).where(BOM.product_id == bom_in.product_id)
    ).scalar_one()
    next_version = max_version + 1
    bom_code = f"BOM-{product.sku}-V{next_version}"

    # Validate items and units
    bom_items: List[BOMItem] = []
    for it in bom_in.items:
        get_item_metadata(db, it.item_type, it.item_id)
        if not validate_unit(it.item_type.value, it.unit):
            raise HTTPException(
                status_code=400,
                detail=f"Unit '{it.unit}' is invalid for item type '{it.item_type.value}'",
            )
        bom_items.append(
            BOMItem(
                item_type=it.item_type,
                item_id=it.item_id,
                quantity_per_batch=Decimal(str(it.quantity_per_batch)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
                unit=it.unit,
            )
        )

    bom = BOM(
        bom_code=bom_code,
        product_id=bom_in.product_id,
        version=next_version,
        batch_yield_packets=Decimal(str(bom_in.batch_yield_packets)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        tolerance_pct=Decimal(str(bom_in.tolerance_pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        description=bom_in.description,
        status=BOMStatus.DRAFT,
        created_by=user_id,
        items=bom_items,
    )

    db.add(bom)
    db.commit()
    db.refresh(bom)
    return bom


def activate_bom(db: Session, bom_id: str) -> BOM:
    """Activate a BOM version and archive any previous active BOM for the product."""
    bom = db.execute(select(BOM).where(BOM.id == bom_id)).scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    now = datetime.now(timezone.utc)

    # Archive previous active BOMs for this product
    active_boms = db.execute(
        select(BOM).where(
            and_(
                BOM.product_id == bom.product_id,
                BOM.status == BOMStatus.ACTIVE,
                BOM.id != bom.id,
            )
        )
    ).scalars().all()

    for old_bom in active_boms:
        old_bom.status = BOMStatus.ARCHIVED
        old_bom.effective_until = now

    bom.status = BOMStatus.ACTIVE
    bom.effective_from = now
    bom.effective_until = None
    db.commit()
    db.refresh(bom)
    return bom


def archive_bom(db: Session, bom_id: str) -> BOM:
    """Archive a BOM version."""
    bom = db.execute(select(BOM).where(BOM.id == bom_id)).scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    bom.status = BOMStatus.ARCHIVED
    bom.effective_until = datetime.now(timezone.utc)
    db.commit()
    db.refresh(bom)
    return bom


def scale_bom(db: Session, bom_id: str, number_of_batches: Decimal) -> BOMScalingResponse:
    """Calculate planned consumption and expected output scaled by number of batches."""
    bom = db.execute(select(BOM).where(BOM.id == bom_id)).scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    product = db.execute(select(Product).where(Product.id == bom.product_id)).scalar_one()

    nb = Decimal(str(number_of_batches)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if nb <= 0:
        raise HTTPException(status_code=400, detail="Number of batches must be greater than zero")

    expected_output = (Decimal(str(bom.batch_yield_packets)) * nb).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    planned_items: List[BOMPlannedItem] = []
    for item in bom.items:
        meta = get_item_metadata(db, item.item_type, item.item_id)
        qty_per_batch = Decimal(str(item.quantity_per_batch))
        planned_qty = (qty_per_batch * nb).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Look up available stock in inventory ledger
        available_stock = get_stock_balance(db, item.item_type, item.item_id)
        is_sufficient = available_stock >= planned_qty

        planned_items.append(
            BOMPlannedItem(
                item_type=item.item_type,
                item_id=item.item_id,
                item_code=meta["code"],
                item_name=meta["name"],
                quantity_per_batch=qty_per_batch,
                planned_quantity=planned_qty,
                unit=item.unit,
                available_stock=available_stock,
                is_sufficient=is_sufficient,
            )
        )

    return BOMScalingResponse(
        bom_id=bom.id,
        bom_code=bom.bom_code,
        version=bom.version,
        product_id=product.id,
        product_name=product.product_name,
        product_sku=product.sku,
        number_of_batches=nb,
        batch_yield_packets=Decimal(str(bom.batch_yield_packets)),
        expected_output_packets=expected_output,
        tolerance_pct=Decimal(str(bom.tolerance_pct)),
        items=planned_items,
    )


def list_boms(
    db: Session,
    product_id: Optional[str] = None,
    status: Optional[BOMStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[BOMOut], int]:
    """Retrieve paginated BOMs with metadata."""
    conditions = []
    if product_id:
        conditions.append(BOM.product_id == product_id)
    if status:
        conditions.append(BOM.status == status)
    if search:
        conditions.append(
            or_(
                BOM.bom_code.ilike(f"%{search}%"),
                BOM.description.ilike(f"%{search}%"),
            )
        )

    query = select(BOM)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count(BOM.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = db.execute(count_query).scalar_one()

    offset = (page - 1) * limit
    boms = db.execute(
        query.order_by(BOM.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    return [_enrich_bom_out(db, b) for b in boms], total
