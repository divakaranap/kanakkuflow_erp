from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.inventory import (
    StockMovement,
    InventoryBalance,
    InventoryAdjustment,
    InventoryItemType,
    MovementType,
    AdjustmentType,
    AdjustmentStatus,
)
from backend.app.models.raw_material import RawMaterial
from backend.app.models.packaging import PackagingItem
from backend.app.models.product import Product
from backend.app.schemas.inventory import (
    StockSummaryItem,
    StockValuationItem,
    StockValuationSummary,
    StockReconciliationItem,
    StockReconciliationReport,
    StockMovementOut,
    AdjustmentCreate,
    AdjustmentOut,
)


def get_item_metadata(db: Session, item_type: InventoryItemType, item_id: str) -> Dict[str, Any]:
    """Fetch item details (code, name, category, base_unit, reorder_level) based on item_type."""
    if item_type == InventoryItemType.RAW:
        item = db.execute(select(RawMaterial).where(RawMaterial.id == item_id)).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"Raw material {item_id} not found")
        return {
            "code": item.material_code,
            "name": item.material_name,
            "category": item.category.value if hasattr(item.category, "value") else str(item.category),
            "base_unit": item.base_unit,
            "reorder_level": Decimal(str(item.reorder_level)),
        }
    elif item_type == InventoryItemType.PACKAGING:
        item = db.execute(select(PackagingItem).where(PackagingItem.id == item_id)).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"Packaging item {item_id} not found")
        return {
            "code": item.packaging_code,
            "name": item.packaging_name,
            "category": item.category.value if hasattr(item.category, "value") else str(item.category),
            "base_unit": item.base_unit,
            "reorder_level": Decimal(str(item.reorder_level)),
        }
    elif item_type == InventoryItemType.FG:
        item = db.execute(select(Product).where(Product.id == item_id)).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"Product {item_id} not found")
        return {
            "code": item.sku,
            "name": item.product_name,
            "category": item.category.value if hasattr(item.category, "value") else str(item.category),
            "base_unit": item.base_unit,
            "reorder_level": Decimal(str(item.reorder_level)),
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown item type {item_type}")


def get_stock_balance(db: Session, item_type: InventoryItemType, item_id: str, batch_id: Optional[str] = None) -> Decimal:
    """Calculate authoritative stock balance directly from immutable stock_movements ledger."""
    conditions = [
        StockMovement.item_type == item_type,
        StockMovement.item_id == item_id,
    ]
    if batch_id:
        conditions.append(StockMovement.batch_id == batch_id)

    query = select(func.coalesce(func.sum(StockMovement.qty_delta), 0)).where(and_(*conditions))
    balance = db.execute(query).scalar_one()
    return Decimal(str(balance)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def create_stock_movement(
    db: Session,
    item_type: InventoryItemType,
    item_id: str,
    movement_type: MovementType,
    qty_delta: Decimal,
    unit_cost_paise: Optional[int] = None,
    total_value_paise: Optional[int] = None,
    source_type: str = "MANUAL",
    source_id: str = "",
    reference_number: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[int] = None,
    batch_id: Optional[str] = None,
) -> StockMovement:
    """Record an immutable stock movement and synchronously update inventory_balances cache."""
    # Ensure item exists
    meta = get_item_metadata(db, item_type, item_id)

    # Convert qty_delta to 4-decimal places
    qty_delta = Decimal(str(qty_delta)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    # Validate against negative inventory if reduction
    current_balance = get_stock_balance(db, item_type, item_id, batch_id)
    if qty_delta < 0 and (current_balance + qty_delta) < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock for {meta['name']} ({meta['code']}). "
                f"Available: {current_balance} {meta['base_unit']}, "
                f"Requested: {abs(qty_delta)} {meta['base_unit']}"
            ),
        )

    # Compute value if cost provided
    if total_value_paise is None and unit_cost_paise is not None:
        total_value_paise = int(round(Decimal(unit_cost_paise) * abs(qty_delta)))

    movement = StockMovement(
        item_type=item_type,
        item_id=item_id,
        batch_id=batch_id,
        movement_type=movement_type,
        qty_delta=qty_delta,
        unit_cost_paise=unit_cost_paise,
        total_value_paise=total_value_paise,
        source_type=source_type,
        source_id=source_id or "00000000-0000-0000-0000-000000000000",
        reference_number=reference_number,
        notes=notes,
        created_by=user_id,
    )
    db.add(movement)
    db.flush()

    # Update inventory_balances cache
    balance_entry = db.execute(
        select(InventoryBalance).where(
            and_(
                InventoryBalance.item_type == item_type,
                InventoryBalance.item_id == item_id,
                InventoryBalance.batch_id == batch_id,
            )
        )
    ).scalar_one_or_none()

    if not balance_entry:
        balance_entry = InventoryBalance(
            item_type=item_type,
            item_id=item_id,
            batch_id=batch_id,
            cached_qty=Decimal("0.0000"),
            total_value_paise=0,
            weighted_avg_rate_paise=0,
        )
        db.add(balance_entry)
        db.flush()

    old_qty = Decimal(str(balance_entry.cached_qty))
    old_value = balance_entry.total_value_paise
    new_qty = old_qty + qty_delta

    if qty_delta > 0:
        added_val = total_value_paise or (int(round(Decimal(unit_cost_paise or 0) * qty_delta)))
        new_val = old_value + added_val
        new_rate = int(round(Decimal(new_val) / new_qty)) if new_qty > 0 else 0
    else:
        # Stock reduction: preserve existing moving weighted average rate
        if old_qty > 0:
            rate = Decimal(old_value) / old_qty
            deducted_val = int(round(rate * abs(qty_delta)))
            new_val = max(0, old_value - deducted_val)
            new_rate = balance_entry.weighted_avg_rate_paise
        else:
            new_val = 0
            new_rate = 0

    balance_entry.cached_qty = new_qty
    balance_entry.total_value_paise = new_val
    balance_entry.weighted_avg_rate_paise = new_rate
    balance_entry.last_reconciled_at = datetime.now(timezone.utc)
    db.flush()

    return movement


def initialize_opening_stock(
    db: Session,
    item_type: InventoryItemType,
    item_id: str,
    quantity: Decimal,
    unit_cost_paise: int,
    user_id: Optional[int] = None,
    notes: Optional[str] = "Opening stock initialization",
    batch_id: Optional[str] = None,
    reference_number: Optional[str] = "OPENING",
) -> StockMovement:
    """Initialize opening stock for an item. Prevent duplicate opening initialization."""
    # Check if OPENING movement already exists
    existing = db.execute(
        select(StockMovement).where(
            and_(
                StockMovement.item_type == item_type,
                StockMovement.item_id == item_id,
                StockMovement.movement_type == MovementType.OPENING,
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opening stock has already been initialized for {item_type.value} item {item_id}",
        )

    qty = Decimal(str(quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="Opening stock quantity must be greater than zero")

    total_val = int(round(Decimal(unit_cost_paise) * qty))

    movement = create_stock_movement(
        db=db,
        item_type=item_type,
        item_id=item_id,
        movement_type=MovementType.OPENING,
        qty_delta=qty,
        unit_cost_paise=unit_cost_paise,
        total_value_paise=total_val,
        source_type="OPENING",
        source_id=item_id,
        reference_number=reference_number or "OPENING",
        notes=notes,
        user_id=user_id,
        batch_id=batch_id,
    )
    db.commit()
    return movement


def get_stock_summary(
    db: Session,
    item_type: Optional[InventoryItemType] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
) -> List[StockSummaryItem]:
    """Return consolidated stock summary across Raw Materials, Packaging, and Finished Goods."""
    items_to_query: List[Tuple[InventoryItemType, Any]] = []

    if not item_type or item_type == InventoryItemType.RAW:
        raw_query = select(RawMaterial).where(RawMaterial.is_active == True)
        if search:
            raw_query = raw_query.where(
                or_(
                    RawMaterial.material_name.ilike(f"%{search}%"),
                    RawMaterial.material_code.ilike(f"%{search}%"),
                )
            )
        for rm in db.execute(raw_query).scalars().all():
            items_to_query.append((InventoryItemType.RAW, rm))

    if not item_type or item_type == InventoryItemType.PACKAGING:
        pkg_query = select(PackagingItem).where(PackagingItem.is_active == True)
        if search:
            pkg_query = pkg_query.where(
                or_(
                    PackagingItem.packaging_name.ilike(f"%{search}%"),
                    PackagingItem.packaging_code.ilike(f"%{search}%"),
                )
            )
        for pkg in db.execute(pkg_query).scalars().all():
            items_to_query.append((InventoryItemType.PACKAGING, pkg))

    if not item_type or item_type == InventoryItemType.FG:
        fg_query = select(Product).where(Product.is_active == True)
        if search:
            fg_query = fg_query.where(
                or_(
                    Product.product_name.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                )
            )
        for prod in db.execute(fg_query).scalars().all():
            items_to_query.append((InventoryItemType.FG, prod))

    result: List[StockSummaryItem] = []

    for itype, obj in items_to_query:
        if itype == InventoryItemType.RAW:
            code = obj.material_code
            name = obj.material_name
            cat = obj.category.value if hasattr(obj.category, "value") else str(obj.category)
            unit = obj.base_unit
            reorder = Decimal(str(obj.reorder_level))
        elif itype == InventoryItemType.PACKAGING:
            code = obj.packaging_code
            name = obj.packaging_name
            cat = obj.category.value if hasattr(obj.category, "value") else str(obj.category)
            unit = obj.base_unit
            reorder = Decimal(str(obj.reorder_level))
        else:
            code = obj.sku
            name = obj.product_name
            cat = obj.category.value if hasattr(obj.category, "value") else str(obj.category)
            unit = obj.base_unit
            reorder = Decimal(str(obj.reorder_level))

        # Check balance in cache or ledger
        bal = db.execute(
            select(InventoryBalance).where(
                and_(
                    InventoryBalance.item_type == itype,
                    InventoryBalance.item_id == obj.id,
                )
            )
        ).scalar_one_or_none()

        if bal:
            current_qty = Decimal(str(bal.cached_qty))
            rate = bal.weighted_avg_rate_paise
            valuation = bal.total_value_paise
            updated_at = bal.updated_at
        else:
            # Fall back to calculating from ledger
            current_qty = get_stock_balance(db, itype, obj.id)
            rate = 0
            valuation = 0
            updated_at = None

        is_low = current_qty <= reorder

        if low_stock_only and not is_low:
            continue

        result.append(
            StockSummaryItem(
                item_type=itype,
                item_id=obj.id,
                item_code=code,
                item_name=name,
                category=cat,
                base_unit=unit,
                current_stock=current_qty,
                reorder_level=reorder,
                is_low_stock=is_low,
                weighted_avg_rate_paise=rate,
                total_valuation_paise=valuation,
                last_updated=updated_at,
            )
        )

    return result


def get_stock_valuation(
    db: Session,
    item_type: Optional[InventoryItemType] = None,
    item_id: Optional[str] = None,
) -> StockValuationSummary:
    """Return inventory valuation using moving weighted average cost."""
    summary_items = get_stock_summary(db, item_type=item_type)
    if item_id:
        summary_items = [it for it in summary_items if it.item_id == item_id]

    items: List[StockValuationItem] = []
    total_val = 0
    raw_val = 0
    pkg_val = 0
    fg_val = 0

    for s in summary_items:
        val_item = StockValuationItem(
            item_type=s.item_type,
            item_id=s.item_id,
            item_code=s.item_code,
            item_name=s.item_name,
            base_unit=s.base_unit,
            quantity=s.current_stock,
            weighted_avg_rate_paise=s.weighted_avg_rate_paise,
            total_value_paise=s.total_valuation_paise,
        )
        items.append(val_item)
        total_val += s.total_valuation_paise
        if s.item_type == InventoryItemType.RAW:
            raw_val += s.total_valuation_paise
        elif s.item_type == InventoryItemType.PACKAGING:
            pkg_val += s.total_valuation_paise
        elif s.item_type == InventoryItemType.FG:
            fg_val += s.total_valuation_paise

    return StockValuationSummary(
        total_valuation_paise=total_val,
        total_items=len(items),
        raw_materials_valuation_paise=raw_val,
        packaging_valuation_paise=pkg_val,
        finished_goods_valuation_paise=fg_val,
        items=items,
    )


def get_stock_ledger(
    db: Session,
    item_type: Optional[InventoryItemType] = None,
    item_id: Optional[str] = None,
    movement_type: Optional[MovementType] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[StockMovementOut], int]:
    """Retrieve historical stock movements with pagination and metadata enrichment."""
    conditions = []
    if item_type:
        conditions.append(StockMovement.item_type == item_type)
    if item_id:
        conditions.append(StockMovement.item_id == item_id)
    if movement_type:
        conditions.append(StockMovement.movement_type == movement_type)
    if from_date:
        conditions.append(StockMovement.created_at >= from_date)
    if to_date:
        conditions.append(StockMovement.created_at <= to_date)

    query = select(StockMovement)
    if conditions:
        query = query.where(and_(*conditions))

    # Total count
    count_query = select(func.count(StockMovement.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = db.execute(count_query).scalar_one()

    # Pagination
    offset = (page - 1) * limit
    movements = db.execute(
        query.order_by(StockMovement.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    # Cache metadata for efficiency
    meta_cache: Dict[str, Dict[str, Any]] = {}

    out_list: List[StockMovementOut] = []
    for m in movements:
        cache_key = f"{m.item_type}_{m.item_id}"
        if cache_key not in meta_cache:
            try:
                meta_cache[cache_key] = get_item_metadata(db, m.item_type, m.item_id)
            except Exception:
                meta_cache[cache_key] = {"code": "UNKNOWN", "name": "Unknown Item"}
        
        meta = meta_cache[cache_key]
        out_list.append(
            StockMovementOut(
                id=m.id,
                item_type=m.item_type,
                item_id=m.item_id,
                item_name=meta["name"],
                item_code=meta["code"],
                batch_id=m.batch_id,
                movement_type=m.movement_type,
                qty_delta=Decimal(str(m.qty_delta)),
                unit_cost_paise=m.unit_cost_paise,
                total_value_paise=m.total_value_paise,
                source_type=m.source_type,
                source_id=m.source_id,
                reference_number=m.reference_number,
                notes=m.notes,
                created_by=m.created_by,
                created_at=m.created_at,
            )
        )

    return out_list, total


def reconcile_inventory(db: Session) -> StockReconciliationReport:
    """Compare authoritative ledger balances SUM(qty_delta) against cached balances and synchronize."""
    summary_items = get_stock_summary(db)
    reconciled_items: List[StockReconciliationItem] = []
    matched = 0
    mismatched = 0

    now = datetime.now(timezone.utc)

    for s in summary_items:
        # 1. Authoritative ledger balance
        ledger_qty = get_stock_balance(db, s.item_type, s.item_id)

        # 2. Cached entry
        cache_entry = db.execute(
            select(InventoryBalance).where(
                and_(
                    InventoryBalance.item_type == s.item_type,
                    InventoryBalance.item_id == s.item_id,
                )
            )
        ).scalar_one_or_none()

        cached_qty = Decimal(str(cache_entry.cached_qty)) if cache_entry else Decimal("0.0000")
        diff = ledger_qty - cached_qty

        if diff == Decimal("0.0000"):
            status_str = "MATCHED"
            matched += 1
        else:
            status_str = "MISMATCH"
            mismatched += 1
            # Synchronize cache
            if cache_entry:
                cache_entry.cached_qty = ledger_qty
                cache_entry.last_reconciled_at = now
            else:
                cache_entry = InventoryBalance(
                    item_type=s.item_type,
                    item_id=s.item_id,
                    cached_qty=ledger_qty,
                    total_value_paise=0,
                    weighted_avg_rate_paise=0,
                    last_reconciled_at=now,
                )
                db.add(cache_entry)

        if cache_entry:
            cache_entry.last_reconciled_at = now

        reconciled_items.append(
            StockReconciliationItem(
                item_type=s.item_type,
                item_id=s.item_id,
                item_code=s.item_code,
                item_name=s.item_name,
                base_unit=s.base_unit,
                ledger_qty=ledger_qty,
                cached_qty=cached_qty,
                difference=diff,
                status=status_str,
            )
        )

    db.commit()

    return StockReconciliationReport(
        reconciled_at=now,
        total_items=len(reconciled_items),
        matched_items=matched,
        mismatched_items=mismatched,
        is_fully_reconciled=(mismatched == 0),
        items=reconciled_items,
    )


def create_adjustment(db: Session, adj_in: AdjustmentCreate, user_id: int) -> InventoryAdjustment:
    """Create a draft inventory adjustment."""
    meta = get_item_metadata(db, adj_in.item_type, adj_in.item_id)

    # Generate adjustment number ADJ-YYYYMMDD-XXXX
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    count_today = db.execute(
        select(func.count(InventoryAdjustment.id)).where(
            InventoryAdjustment.adjustment_number.like(f"ADJ-{today_str}-%")
        )
    ).scalar_one()
    adj_number = f"ADJ-{today_str}-{(count_today + 1):04d}"

    adjustment = InventoryAdjustment(
        adjustment_number=adj_number,
        item_type=adj_in.item_type,
        item_id=adj_in.item_id,
        adjustment_type=adj_in.adjustment_type,
        quantity=Decimal(str(adj_in.quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        reason=adj_in.reason,
        reference_number=adj_in.reference_number,
        status=AdjustmentStatus.DRAFT,
        created_by=user_id,
    )
    db.add(adjustment)
    db.commit()
    db.refresh(adjustment)
    return adjustment


def post_adjustment(db: Session, adjustment_id: str, user_id: int) -> InventoryAdjustment:
    """Post an inventory adjustment, generating atomic stock movement."""
    adj = db.execute(
        select(InventoryAdjustment).where(InventoryAdjustment.id == adjustment_id)
    ).scalar_one_or_none()

    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")

    if adj.status != AdjustmentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT adjustments can be posted")

    qty = Decimal(str(adj.quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    qty_delta = qty if adj.adjustment_type == AdjustmentType.INCREASE else -qty

    # Look up current item valuation rate for costing
    bal = db.execute(
        select(InventoryBalance).where(
            and_(
                InventoryBalance.item_type == adj.item_type,
                InventoryBalance.item_id == adj.item_id,
            )
        )
    ).scalar_one_or_none()
    unit_cost = bal.weighted_avg_rate_paise if bal else 0

    create_stock_movement(
        db=db,
        item_type=adj.item_type,
        item_id=adj.item_id,
        movement_type=MovementType.ADJUSTMENT,
        qty_delta=qty_delta,
        unit_cost_paise=unit_cost,
        source_type="ADJUSTMENT",
        source_id=adj.id,
        reference_number=adj.adjustment_number,
        notes=f"Adjustment: {adj.reason}",
        user_id=user_id,
    )

    adj.status = AdjustmentStatus.POSTED
    adj.approved_by = user_id
    adj.posted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(adj)
    return adj


def list_adjustments(
    db: Session,
    item_type: Optional[InventoryItemType] = None,
    status: Optional[AdjustmentStatus] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[AdjustmentOut], int]:
    """List adjustments with metadata enrichment."""
    conditions = []
    if item_type:
        conditions.append(InventoryAdjustment.item_type == item_type)
    if status:
        conditions.append(InventoryAdjustment.status == status)

    query = select(InventoryAdjustment)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count(InventoryAdjustment.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = db.execute(count_query).scalar_one()

    offset = (page - 1) * limit
    adjs = db.execute(
        query.order_by(InventoryAdjustment.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    meta_cache: Dict[str, Dict[str, Any]] = {}
    out_list: List[AdjustmentOut] = []
    for a in adjs:
        cache_key = f"{a.item_type}_{a.item_id}"
        if cache_key not in meta_cache:
            try:
                meta_cache[cache_key] = get_item_metadata(db, a.item_type, a.item_id)
            except Exception:
                meta_cache[cache_key] = {"code": "UNKNOWN", "name": "Unknown Item"}
        meta = meta_cache[cache_key]

        out_list.append(
            AdjustmentOut(
                id=a.id,
                adjustment_number=a.adjustment_number,
                item_type=a.item_type,
                item_id=a.item_id,
                item_name=meta["name"],
                item_code=meta["code"],
                adjustment_type=a.adjustment_type,
                quantity=Decimal(str(a.quantity)),
                reason=a.reason,
                reference_number=a.reference_number,
                status=a.status,
                created_by=a.created_by,
                approved_by=a.approved_by,
                posted_at=a.posted_at,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )

    return out_list, total
