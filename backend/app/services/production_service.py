from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.production import (
    ProductionRun,
    ProductionRunMaterial,
    ProductionRunOverhead,
    ProductionRunStatus,
    OverheadExpenseType,
    VarianceStatus,
)
from backend.app.models.bom import BOM, BOMStatus
from backend.app.models.product import Product
from backend.app.models.inventory import InventoryItemType, MovementType
from backend.app.schemas.production import (
    ProductionRunCreate,
    ProductionRunUpdate,
    ProductionRunOut,
    ProductionRunMaterialOut,
    ProductionRunOverheadOut,
    ProductionVarianceReport,
    ProductionCostingReport,
)
from backend.app.services.bom_service import get_active_bom, create_bom_snapshot
from backend.app.services.inventory_service import (
    get_stock_balance,
    create_stock_movement,
    get_item_metadata,
)
from backend.app.services.variance_service import (
    calculate_variance_pct,
    analyze_production_run_variance,
)
from backend.app.services.costing_service import (
    calculate_production_run_costing,
    get_applicable_unit_cost,
)


def _enrich_production_run_out(db: Session, run: ProductionRun) -> ProductionRunOut:
    """Enrich production run with product, BOM, material codes and names."""
    product = db.execute(select(Product).where(Product.id == run.product_id)).scalar_one_or_none()
    product_name = product.product_name if product else "Unknown Product"
    product_sku = product.sku if product else "UNKNOWN"

    bom = db.execute(select(BOM).where(BOM.id == run.bom_id)).scalar_one_or_none()
    bom_code = bom.bom_code if bom else "UNKNOWN"

    materials_out: List[ProductionRunMaterialOut] = []
    for m in run.materials:
        try:
            meta = get_item_metadata(db, m.item_type, m.item_id)
            code, name = meta["code"], meta["name"]
        except Exception:
            code, name = "UNKNOWN", "Unknown Item"

        materials_out.append(
            ProductionRunMaterialOut(
                id=m.id,
                production_run_id=m.production_run_id,
                item_type=m.item_type,
                item_id=m.item_id,
                item_name=name,
                item_code=code,
                planned_quantity=Decimal(str(m.planned_quantity)),
                issued_quantity=Decimal(str(m.issued_quantity)),
                consumed_quantity=Decimal(str(m.consumed_quantity)),
                unit=m.unit,
                planned_unit_cost=m.planned_unit_cost,
                actual_unit_cost=m.actual_unit_cost,
                material_cost_paise=m.material_cost_paise,
                consumption_variance_pct=Decimal(str(m.consumption_variance_pct)),
            )
        )

    overheads_out: List[ProductionRunOverheadOut] = []
    for o in run.overheads:
        overheads_out.append(
            ProductionRunOverheadOut(
                id=o.id,
                production_run_id=o.production_run_id,
                expense_type=o.expense_type,
                amount_paise=o.amount_paise,
                description=o.description,
                created_at=o.created_at,
            )
        )

    return ProductionRunOut(
        id=run.id,
        run_number=run.run_number,
        product_id=run.product_id,
        product_name=product_name,
        product_sku=product_sku,
        bom_id=run.bom_id,
        bom_code=bom_code,
        production_date=run.production_date,
        batch_number=run.batch_number,
        number_of_batches=Decimal(str(run.number_of_batches)),
        expected_output=Decimal(str(run.expected_output)),
        actual_good_output=Decimal(str(run.actual_good_output)),
        damaged_packaging=Decimal(str(run.damaged_packaging)),
        wastage_quantity=Decimal(str(run.wastage_quantity)),
        status=run.status,
        planned_material_cost_paise=run.planned_material_cost_paise,
        actual_material_cost_paise=run.actual_material_cost_paise,
        packaging_cost_paise=run.packaging_cost_paise,
        labour_cost_paise=run.labour_cost_paise,
        utility_cost_paise=run.utility_cost_paise,
        total_production_cost_paise=run.total_production_cost_paise,
        cost_per_packet_paise=run.cost_per_packet_paise,
        cost_per_packet_decimal=Decimal(str(run.cost_per_packet_decimal)),
        variance_status=run.variance_status,
        notes=run.notes,
        supervisor_id=run.supervisor_id,
        created_at=run.created_at,
        posted_at=run.posted_at,
        materials=materials_out,
        overheads=overheads_out,
    )


def create_production_run(db: Session, run_in: ProductionRunCreate, user_id: int) -> ProductionRun:
    """Create a new draft production run based on active BOM."""
    product = db.execute(select(Product).where(Product.id == run_in.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {run_in.product_id} not found")

    # Load active or specified BOM
    if run_in.bom_id:
        bom = db.execute(select(BOM).where(BOM.id == run_in.bom_id)).scalar_one_or_none()
        if not bom:
            raise HTTPException(status_code=404, detail=f"BOM {run_in.bom_id} not found")
    else:
        bom = get_active_bom(db, run_in.product_id, run_in.production_date)

    # Scale expected output
    nb = Decimal(str(run_in.number_of_batches)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_output = (Decimal(str(bom.batch_yield_packets)) * nb).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    # Generate unique run number PR-YYYYMMDD-XXXX
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    count_today = db.execute(
        select(func.count(ProductionRun.id)).where(ProductionRun.run_number.like(f"PR-{today_str}-%"))
    ).scalar_one()
    run_number = f"PR-{today_str}-{(count_today + 1):04d}"

    # Take immutable snapshot of BOM
    snapshot = create_bom_snapshot(db, bom)

    # Build materials list from BOM and incoming actuals
    materials: List[ProductionRunMaterial] = []
    actual_materials_map = {m.item_id: m for m in (run_in.materials or [])}

    planned_total_cost = 0

    for b_item in bom.items:
        planned_q = (Decimal(str(b_item.quantity_per_batch)) * nb).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        rounded_cost, exact_cost = get_applicable_unit_cost(db, b_item.item_type, b_item.item_id)
        planned_total_cost += int(round(planned_q * exact_cost))

        actual_input = actual_materials_map.get(b_item.item_id)
        if actual_input:
            issued_q = Decimal(str(actual_input.issued_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            consumed_q = (
                Decimal(str(actual_input.consumed_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                if actual_input.consumed_quantity is not None
                else issued_q
            )
            unit_str = actual_input.unit
        else:
            issued_q = planned_q
            consumed_q = planned_q
            unit_str = b_item.unit

        var_pct = calculate_variance_pct(consumed_q, planned_q)

        materials.append(
            ProductionRunMaterial(
                item_type=b_item.item_type,
                item_id=b_item.item_id,
                planned_quantity=planned_q,
                issued_quantity=issued_q,
                consumed_quantity=consumed_q,
                unit=unit_str,
                planned_unit_cost=rounded_cost,
                actual_unit_cost=rounded_cost,
                material_cost_paise=int(round(consumed_q * exact_cost)),
                consumption_variance_pct=var_pct,
            )
        )

    # Overheads
    overheads: List[ProductionRunOverhead] = []
    for ov in (run_in.overheads or []):
        overheads.append(
            ProductionRunOverhead(
                expense_type=ov.expense_type,
                amount_paise=ov.amount_paise,
                description=ov.description,
            )
        )

    good_output = Decimal(str(run_in.actual_good_output)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    damaged_pkg = Decimal(str(run_in.damaged_packaging)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    wastage_q = Decimal(str(run_in.wastage_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    run = ProductionRun(
        run_number=run_number,
        product_id=run_in.product_id,
        bom_id=bom.id,
        bom_version_snapshot=snapshot,
        production_date=run_in.production_date or datetime.now(timezone.utc),
        batch_number=run_in.batch_number,
        number_of_batches=nb,
        expected_output=expected_output,
        actual_good_output=good_output,
        damaged_packaging=damaged_pkg,
        wastage_quantity=wastage_q,
        status=ProductionRunStatus.DRAFT,
        planned_material_cost_paise=planned_total_cost,
        variance_status=VarianceStatus.NORMAL,
        notes=run_in.notes,
        supervisor_id=user_id,
        materials=materials,
        overheads=overheads,
    )

    db.add(run)
    db.flush()

    # Calculate initial costing and variance
    calculate_production_run_costing(db, run)
    var_rep = analyze_production_run_variance(run)
    run.variance_status = VarianceStatus.WARNING if var_rep.has_alerts else VarianceStatus.NORMAL

    db.commit()
    db.refresh(run)
    return run


def update_production_run(db: Session, run_id: str, run_up: ProductionRunUpdate, user_id: int) -> ProductionRun:
    """Update draft production run quantities, materials, and overheads."""
    run = db.execute(select(ProductionRun).where(ProductionRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")

    if run.status != ProductionRunStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot edit a non-draft production run")

    if run_up.batch_number is not None:
        run.batch_number = run_up.batch_number
    if run_up.actual_good_output is not None:
        run.actual_good_output = Decimal(str(run_up.actual_good_output)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if run_up.damaged_packaging is not None:
        run.damaged_packaging = Decimal(str(run_up.damaged_packaging)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if run_up.wastage_quantity is not None:
        run.wastage_quantity = Decimal(str(run_up.wastage_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if run_up.production_date is not None:
        run.production_date = run_up.production_date
    if run_up.notes is not None:
        run.notes = run_up.notes

    # Update materials if provided
    if run_up.materials is not None:
        actual_map = {m.item_id: m for m in run_up.materials}
        for mat in run.materials:
            if mat.item_id in actual_map:
                in_mat = actual_map[mat.item_id]
                mat.issued_quantity = Decimal(str(in_mat.issued_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                mat.consumed_quantity = (
                    Decimal(str(in_mat.consumed_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                    if in_mat.consumed_quantity is not None
                    else mat.issued_quantity
                )
                mat.unit = in_mat.unit
                mat.consumption_variance_pct = calculate_variance_pct(mat.consumed_quantity, mat.planned_quantity)

    # Update overheads if provided
    if run_up.overheads is not None:
        run.overheads.clear()
        for ov in run_up.overheads:
            run.overheads.append(
                ProductionRunOverhead(
                    expense_type=ov.expense_type,
                    amount_paise=ov.amount_paise,
                    description=ov.description,
                )
            )

    # Recalculate costing and variance
    calculate_production_run_costing(db, run)
    var_rep = analyze_production_run_variance(run)
    run.variance_status = VarianceStatus.WARNING if var_rep.has_alerts else VarianceStatus.NORMAL

    db.commit()
    db.refresh(run)
    return run


def post_production_run(db: Session, run_id: str, user_id: int) -> ProductionRun:
    """
    Post production run:
    1. Validates available stock for each material to prevent negative inventory.
    2. Atomically records stock ledger movements:
       - RAW MATERIALS: PRODUCTION_ISSUE (negative qty_delta)
       - PACKAGING: PRODUCTION_ISSUE (negative qty_delta)
       - DAMAGED PACKAGING: PRODUCTION_SCRAP (negative qty_delta)
       - FINISHED GOODS: PRODUCTION_OUTPUT (positive qty_delta)
    3. Finalizes costing and updates run status to POSTED.
    """
    run = db.execute(select(ProductionRun).where(ProductionRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")

    if run.status != ProductionRunStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Cannot post production run with status {run.status.value}")

    # 1. Stock validation across all materials to guarantee atomic execution
    for m in run.materials:
        avail_stock = get_stock_balance(db, m.item_type, m.item_id)
        if avail_stock < m.consumed_quantity:
            meta = get_item_metadata(db, m.item_type, m.item_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient inventory for {meta['name']} ({meta['code']}). "
                    f"Available: {avail_stock} {m.unit}, Required: {m.consumed_quantity} {m.unit}"
                ),
            )

    # 2. Finalize costing calculations
    calculate_production_run_costing(db, run)
    var_rep = analyze_production_run_variance(run)
    run.variance_status = VarianceStatus.WARNING if var_rep.has_alerts else VarianceStatus.NORMAL

    # 3. Atomic stock movement creation
    for m in run.materials:
        consumed_q = Decimal(str(m.consumed_quantity))

        if m.item_type == InventoryItemType.RAW:
            create_stock_movement(
                db=db,
                item_type=InventoryItemType.RAW,
                item_id=m.item_id,
                movement_type=MovementType.PRODUCTION_ISSUE,
                qty_delta=-consumed_q,
                unit_cost_paise=m.actual_unit_cost,
                total_value_paise=m.material_cost_paise,
                source_type="PRODUCTION_RUN",
                source_id=run.id,
                reference_number=run.run_number,
                notes=f"Production issue for run {run.run_number} (batch {run.batch_number})",
                user_id=user_id,
            )
        elif m.item_type == InventoryItemType.PACKAGING:
            # Distinguish scrap/damaged packaging if primary pouch
            is_pouch = "pouch" in m.unit.lower() or "piece" in m.unit.lower()
            damaged_q = Decimal(str(run.damaged_packaging))

            if is_pouch and damaged_q > Decimal("0") and consumed_q >= damaged_q:
                good_pkg_q = consumed_q - damaged_q
                if good_pkg_q > Decimal("0"):
                    create_stock_movement(
                        db=db,
                        item_type=InventoryItemType.PACKAGING,
                        item_id=m.item_id,
                        movement_type=MovementType.PRODUCTION_ISSUE,
                        qty_delta=-good_pkg_q,
                        unit_cost_paise=m.actual_unit_cost,
                        total_value_paise=int(round(good_pkg_q * Decimal(str(m.actual_unit_cost)))),
                        source_type="PRODUCTION_RUN",
                        source_id=run.id,
                        reference_number=run.run_number,
                        notes=f"Packaging issue for run {run.run_number}",
                        user_id=user_id,
                    )
                create_stock_movement(
                    db=db,
                    item_type=InventoryItemType.PACKAGING,
                    item_id=m.item_id,
                    movement_type=MovementType.PRODUCTION_SCRAP,
                    qty_delta=-damaged_q,
                    unit_cost_paise=m.actual_unit_cost,
                    total_value_paise=int(round(damaged_q * Decimal(str(m.actual_unit_cost)))),
                    source_type="PRODUCTION_RUN",
                    source_id=run.id,
                    reference_number=run.run_number,
                    notes=f"Damaged packaging scrap for run {run.run_number}",
                    user_id=user_id,
                )
            else:
                create_stock_movement(
                    db=db,
                    item_type=InventoryItemType.PACKAGING,
                    item_id=m.item_id,
                    movement_type=MovementType.PRODUCTION_ISSUE,
                    qty_delta=-consumed_q,
                    unit_cost_paise=m.actual_unit_cost,
                    total_value_paise=m.material_cost_paise,
                    source_type="PRODUCTION_RUN",
                    source_id=run.id,
                    reference_number=run.run_number,
                    notes=f"Packaging issue for run {run.run_number}",
                    user_id=user_id,
                )

    # 4. Finished Goods stock increase
    good_out = Decimal(str(run.actual_good_output))
    if good_out > Decimal("0"):
        create_stock_movement(
            db=db,
            item_type=InventoryItemType.FG,
            item_id=run.product_id,
            movement_type=MovementType.PRODUCTION_OUTPUT,
            qty_delta=good_out,
            unit_cost_paise=run.cost_per_packet_paise,
            total_value_paise=run.total_production_cost_paise,
            source_type="PRODUCTION_RUN",
            source_id=run.id,
            reference_number=run.run_number,
            notes=f"Finished goods output for run {run.run_number} ({good_out} packets)",
            user_id=user_id,
        )

    run.status = ProductionRunStatus.POSTED
    run.posted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def get_production_run(db: Session, run_id: str) -> ProductionRunOut:
    """Retrieve enriched production run by ID."""
    run = db.execute(select(ProductionRun).where(ProductionRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return _enrich_production_run_out(db, run)


def list_production_runs(
    db: Session,
    product_id: Optional[str] = None,
    status: Optional[ProductionRunStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[ProductionRunOut], int]:
    """Retrieve paginated production runs."""
    conditions = []
    if product_id:
        conditions.append(ProductionRun.product_id == product_id)
    if status:
        conditions.append(ProductionRun.status == status)
    if search:
        conditions.append(
            or_(
                ProductionRun.run_number.ilike(f"%{search}%"),
                ProductionRun.batch_number.ilike(f"%{search}%"),
            )
        )

    query = select(ProductionRun)
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count(ProductionRun.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = db.execute(count_query).scalar_one()

    offset = (page - 1) * limit
    runs = db.execute(
        query.order_by(ProductionRun.production_date.desc(), ProductionRun.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return [_enrich_production_run_out(db, r) for r in runs], total


def get_production_summary(db: Session) -> Dict[str, Any]:
    """Retrieve high-level production metrics for dashboard."""
    total_runs = db.execute(select(func.count(ProductionRun.id))).scalar_one()
    posted_runs = db.execute(
        select(func.count(ProductionRun.id)).where(ProductionRun.status == ProductionRunStatus.POSTED)
    ).scalar_one()

    total_good_output = db.execute(
        select(func.coalesce(func.sum(ProductionRun.actual_good_output), 0)).where(
            ProductionRun.status == ProductionRunStatus.POSTED
        )
    ).scalar_one()

    total_expected_output = db.execute(
        select(func.coalesce(func.sum(ProductionRun.expected_output), 0)).where(
            ProductionRun.status == ProductionRunStatus.POSTED
        )
    ).scalar_one()

    total_production_cost = db.execute(
        select(func.coalesce(func.sum(ProductionRun.total_production_cost_paise), 0)).where(
            ProductionRun.status == ProductionRunStatus.POSTED
        )
    ).scalar_one()

    avg_cost_per_packet = (
        int(round(Decimal(total_production_cost) / Decimal(str(total_good_output))))
        if total_good_output > Decimal("0")
        else 0
    )

    alert_runs = db.execute(
        select(func.count(ProductionRun.id)).where(
            and_(
                ProductionRun.status == ProductionRunStatus.POSTED,
                ProductionRun.variance_status != VarianceStatus.NORMAL,
            )
        )
    ).scalar_one()

    return {
        "total_runs": total_runs,
        "posted_runs": posted_runs,
        "total_good_packets_produced": float(total_good_output),
        "total_expected_packets": float(total_expected_output),
        "overall_yield_pct": (
            float(round((Decimal(str(total_good_output)) / Decimal(str(total_expected_output))) * 100, 2))
            if total_expected_output > Decimal("0")
            else 100.0
        ),
        "total_production_cost_paise": total_production_cost,
        "avg_cost_per_packet_paise": avg_cost_per_packet,
        "runs_with_variance_alerts": alert_runs,
    }
