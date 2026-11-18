from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from backend.app.models.production import ProductionRun, ProductionRunMaterial, OverheadExpenseType
from backend.app.models.inventory import InventoryBalance, InventoryItemType
from backend.app.models.product import Product
from backend.app.schemas.production import ProductionCostingReport
from backend.app.services.inventory_service import get_item_metadata


def get_applicable_unit_cost(db: Session, item_type: InventoryItemType, item_id: str) -> Tuple[int, Decimal]:
    """
    Retrieve moving weighted-average valuation rate from inventory_balances.
    Returns (unit_cost_paise_rounded, exact_unit_cost_decimal).
    """
    bal = db.execute(
        select(InventoryBalance).where(
            and_(
                InventoryBalance.item_type == item_type,
                InventoryBalance.item_id == item_id,
            )
        )
    ).scalar_one_or_none()

    if not bal or bal.cached_qty <= Decimal("0"):
        # Fall back to standard/cached rate
        rate = Decimal(str(bal.weighted_avg_rate_paise if bal else 0))
        return int(rate), rate

    # High-precision exact rate: total_value / cached_qty
    exact_rate = Decimal(bal.total_value_paise) / Decimal(str(bal.cached_qty))
    rounded_paise = int(round(exact_rate))
    return rounded_paise, exact_rate


def calculate_production_run_costing(db: Session, run: ProductionRun) -> ProductionCostingReport:
    """
    Calculate comprehensive production costing based on actual consumption,
    moving weighted average rates, and direct production overheads.
    """
    raw_materials_cost = 0
    packaging_cost = 0
    breakdown: List[Dict[str, Any]] = []

    for m in run.materials:
        consumed_qty = Decimal(str(m.consumed_quantity))
        rounded_rate, exact_rate = get_applicable_unit_cost(db, m.item_type, m.item_id)

        # Cost in paise using exact moving weighted-average rate
        line_cost_paise = int(round(consumed_qty * exact_rate))
        m.material_cost_paise = line_cost_paise
        m.actual_unit_cost = rounded_rate

        meta = get_item_metadata(db, m.item_type, m.item_id)

        if m.item_type == InventoryItemType.RAW:
            raw_materials_cost += line_cost_paise
        elif m.item_type == InventoryItemType.PACKAGING:
            packaging_cost += line_cost_paise

        breakdown.append({
            "item_type": m.item_type.value,
            "item_id": m.item_id,
            "item_code": meta["code"],
            "item_name": meta["name"],
            "consumed_quantity": str(consumed_qty),
            "unit": m.unit,
            "unit_cost_paise": rounded_rate,
            "line_cost_paise": line_cost_paise,
        })

    # Direct production overheads
    labour_cost = sum(o.amount_paise for o in run.overheads if o.expense_type == OverheadExpenseType.LABOUR)
    utility_cost = sum(
        o.amount_paise for o in run.overheads if o.expense_type in (OverheadExpenseType.GAS, OverheadExpenseType.POWER)
    )
    other_overhead = sum(o.amount_paise for o in run.overheads if o.expense_type == OverheadExpenseType.OTHER)
    total_overheads = labour_cost + utility_cost + other_overhead

    total_mat_cost = raw_materials_cost + packaging_cost
    total_cost = total_mat_cost + total_overheads

    # Cost per good packet
    good_output = Decimal(str(run.actual_good_output))
    if good_output > Decimal("0"):
        # cost_per_packet_dec in Rupees (e.g. ₹31.1436)
        cost_per_packet_dec = (Decimal(total_cost) / (good_output * Decimal("100"))).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        cost_per_packet_paise = int(round(Decimal(total_cost) / good_output))
    else:
        cost_per_packet_dec = Decimal("0.0000")
        cost_per_packet_paise = 0

    # Selling price and gross margin
    product = db.execute(select(Product).where(Product.id == run.product_id)).scalar_one_or_none()
    selling_price = product.selling_price_paise if product else 0
    margin_paise = selling_price - cost_per_packet_paise
    margin_pct = (
        ((Decimal(margin_paise) / Decimal(selling_price)) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if selling_price > 0
        else Decimal("0.00")
    )

    # Update production run model aggregates
    run.actual_material_cost_paise = raw_materials_cost
    run.packaging_cost_paise = packaging_cost
    run.labour_cost_paise = labour_cost
    run.utility_cost_paise = utility_cost
    run.total_production_cost_paise = total_cost
    run.cost_per_packet_paise = cost_per_packet_paise
    run.cost_per_packet_decimal = cost_per_packet_dec

    return ProductionCostingReport(
        production_run_id=run.id,
        run_number=run.run_number,
        actual_good_output=good_output,
        raw_materials_cost_paise=raw_materials_cost,
        packaging_cost_paise=packaging_cost,
        total_material_cost_paise=total_mat_cost,
        labour_cost_paise=labour_cost,
        utility_cost_paise=utility_cost,
        total_overheads_paise=total_overheads,
        total_production_cost_paise=total_cost,
        cost_per_packet_paise=cost_per_packet_paise,
        cost_per_packet_decimal=cost_per_packet_dec,
        selling_price_paise=selling_price,
        gross_margin_paise=margin_paise,
        gross_margin_pct=margin_pct,
        material_breakdown=breakdown,
    )
