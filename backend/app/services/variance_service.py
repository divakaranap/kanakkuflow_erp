from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from backend.app.models.production import ProductionRun, VarianceStatus
from backend.app.schemas.production import VarianceItem, ProductionVarianceReport


def calculate_variance_pct(actual: Decimal, planned: Decimal) -> Decimal:
    """Calculate percentage variance: ((Actual - Planned) / Planned) * 100."""
    if planned == Decimal("0"):
        return Decimal("0.00") if actual == Decimal("0") else Decimal("100.00")
    var = ((actual - planned) / planned) * Decimal("100")
    return var.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def evaluate_variance_status(variance_pct: Decimal, tolerance_pct: Decimal) -> Tuple[str, bool]:
    """
    Evaluate variance status against tolerance.
    Returns (status_label, is_alert).
    Status labels: 'OK', 'WARNING', 'CRITICAL'.
    """
    abs_var = abs(variance_pct)
    tol = abs(tolerance_pct)

    if abs_var <= tol:
        return "OK", False
    elif abs_var <= (tol * Decimal("2.5")):
        return "WARNING", True
    else:
        return "CRITICAL", True


def analyze_production_run_variance(run: ProductionRun) -> ProductionVarianceReport:
    """
    Generate complete variance analysis for a production run.
    Analyzes yield variance and individual material consumption variances.
    """
    tolerance = Decimal(str(run.bom.tolerance_pct)) if run.bom else Decimal("3.00")

    # 1. Yield variance
    expected_out = Decimal(str(run.expected_output))
    actual_out = Decimal(str(run.actual_good_output))
    yield_diff = actual_out - expected_out
    yield_var_pct = calculate_variance_pct(actual_out, expected_out)
    yield_status, yield_alert = evaluate_variance_status(yield_var_pct, tolerance)

    alerts: List[str] = []
    if yield_alert:
        direction = "above" if yield_var_pct > 0 else "below"
        alerts.append(
            f"Production yield is {abs(yield_var_pct):.2f}% {direction} expectation ({yield_status})"
        )

    # 2. Material consumption variances
    mat_items: List[VarianceItem] = []
    for m in run.materials:
        planned_q = Decimal(str(m.planned_quantity))
        consumed_q = Decimal(str(m.consumed_quantity))
        diff_q = consumed_q - planned_q
        var_pct = calculate_variance_pct(consumed_q, planned_q)
        mat_status, mat_alert = evaluate_variance_status(var_pct, tolerance)

        # Retrieve item name & code if available
        name = getattr(m, "item_name", "Material")
        code = getattr(m, "item_code", m.item_id)

        if mat_alert:
            alerts.append(
                f"{name} ({code}) consumption variance is {var_pct:+.2f}% ({mat_status})"
            )

        mat_items.append(
            VarianceItem(
                item_type=m.item_type.value,
                item_id=m.item_id,
                item_code=code,
                item_name=name,
                planned_quantity=planned_q,
                actual_quantity=consumed_q,
                unit=m.unit,
                difference=diff_q,
                variance_pct=var_pct,
                tolerance_pct=tolerance,
                status=mat_status,
            )
        )

    return ProductionVarianceReport(
        production_run_id=run.id,
        run_number=run.run_number,
        expected_output=expected_out,
        actual_good_output=actual_out,
        yield_difference=yield_diff,
        yield_variance_pct=yield_var_pct,
        yield_status=yield_status,
        material_variances=mat_items,
        has_alerts=len(alerts) > 0,
        alerts=alerts,
    )
