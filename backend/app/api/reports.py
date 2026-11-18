from typing import Optional, Literal
from datetime import date
from io import BytesIO
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import require_roles
from backend.app.models.user import UserRole
from backend.app.services.report_service import (
    get_dashboard_analytics_summary,
    export_table_to_csv,
    export_table_to_excel,
    export_table_to_pdf,
    build_gstr1_sales_register,
    build_gstr2_purchase_register,
    build_stock_ledger_report,
    build_production_yield_report,
    build_receivables_ageing_export_report,
    build_trial_balance_export_report,
)

router = APIRouter(tags=["reports"])


def format_report_response(
    report_title: str,
    headers: list,
    rows: list,
    fmt: str,
    filename_prefix: str,
) -> Response:
    """Format tabular data into requested format (csv, xlsx, pdf)."""
    fmt_lower = fmt.lower()
    timestamp = date.today().strftime("%Y%m%d")

    if fmt_lower == "csv":
        csv_text = export_table_to_csv(headers, rows)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_prefix}_{timestamp}.csv"'},
        )
    elif fmt_lower == "xlsx" or fmt_lower == "excel":
        excel_buf = export_table_to_excel(report_title, headers, rows)
        return StreamingResponse(
            excel_buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename_prefix}_{timestamp}.xlsx"'},
        )
    elif fmt_lower == "pdf":
        pdf_buf = export_table_to_pdf(report_title, headers, rows)
        return StreamingResponse(
            pdf_buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_prefix}_{timestamp}.pdf"'},
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{fmt}'. Choose from 'csv', 'xlsx', or 'pdf'.")


@router.get(
    "/analytics/dashboard-summary",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN, UserRole.PRODUCTION]))],
)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Executive Dashboard summary metrics, KPIs, and operational aggregates."""
    return get_dashboard_analytics_summary(db)


@router.get(
    "/reports/gstr1",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def export_gstr1(
    format: str = Query("csv", description="csv, xlsx, or pdf"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """GSTR-1 Outward Supplies / Sales Register."""
    headers, rows = build_gstr1_sales_register(db, from_date, to_date)
    return format_report_response("GSTR-1 Outward Supplies Register", headers, rows, format, "GSTR1_Sales_Register")


@router.get(
    "/reports/gstr2",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def export_gstr2(
    format: str = Query("csv", description="csv, xlsx, or pdf"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """GSTR-2 Inward Supplies / Purchase Register."""
    headers, rows = build_gstr2_purchase_register(db, from_date, to_date)
    return format_report_response("GSTR-2 Inward Supplies Register", headers, rows, format, "GSTR2_Purchase_Register")


@router.get(
    "/reports/stock-ledger",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
def export_stock_ledger(
    format: str = Query("csv", description="csv, xlsx, or pdf"),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    """Stock Movement Ledger Register."""
    headers, rows = build_stock_ledger_report(db, limit)
    return format_report_response("Stock Movement Ledger Register", headers, rows, format, "Stock_Movement_Ledger")


@router.get(
    "/reports/production-yield",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
def export_production_yield(
    format: str = Query("csv", description="csv, xlsx, or pdf"),
    db: Session = Depends(get_db),
):
    """Production & Yield Variance Report."""
    headers, rows = build_production_yield_report(db)
    return format_report_response("Production & Yield Variance Report", headers, rows, format, "Production_Yield_Report")


@router.get(
    "/reports/receivables-ageing",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN]))],
)
def export_receivables_ageing(
    format: str = Query("csv", description="csv, xlsx, or pdf"),
    db: Session = Depends(get_db),
):
    """Accounts Receivable Ageing Schedule Report."""
    headers, rows = build_receivables_ageing_export_report(db)
    return format_report_response("Accounts Receivable Ageing Report", headers, rows, format, "Receivables_Ageing")


@router.get(
    "/reports/trial-balance",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def export_trial_balance(
    format: str = Query("csv", description="csv, xlsx, or pdf"),
    db: Session = Depends(get_db),
):
    """Trial Balance Financial Report."""
    headers, rows = build_trial_balance_export_report(db)
    return format_report_response("Trial Balance Statement", headers, rows, format, "Trial_Balance")
