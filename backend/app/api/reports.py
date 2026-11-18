from typing import Optional, Literal
from datetime import date
from io import BytesIO
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import require_roles, get_current_user
from backend.app.models.user import User, UserRole
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
    fmt: Optional[str] = "json",
    filename_prefix: str = "Report",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    as_of_date: Optional[date] = None,
) -> Response:
    """Format tabular data into requested format (json, csv, xlsx, pdf) with safe Content-Disposition."""
    # Build date descriptor string for headers & filename
    if from_date and to_date:
        date_info = f"Period: {from_date.isoformat()} to {to_date.isoformat()}"
        file_suffix = f"{from_date.isoformat()}_to_{to_date.isoformat()}"
    elif as_of_date:
        date_info = f"As-of Date: {as_of_date.isoformat()}"
        file_suffix = f"as_of_{as_of_date.isoformat()}"
    else:
        date_info = f"Generated: {date.today().isoformat()}"
        file_suffix = date.today().isoformat()

    full_filename_base = f"KANAKKUFlow_{filename_prefix}_{file_suffix}"

    fmt_lower = (fmt or "json").lower().strip()

    if fmt_lower == "json":
        return JSONResponse(content={
            "title": report_title,
            "date_info": date_info,
            "headers": headers,
            "rows": rows,
            "total_records": max(len(rows) - 1, 0) if (rows and str(rows[-1][0]).upper() == "TOTAL") else len(rows),
        })
    elif fmt_lower == "csv":
        csv_text = export_table_to_csv(headers, rows)
        return Response(
            content=csv_text,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{full_filename_base}.csv"'},
        )
    elif fmt_lower in ["xlsx", "excel"]:
        excel_buf = export_table_to_excel(report_title, headers, rows, date_info=date_info)
        return StreamingResponse(
            excel_buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{full_filename_base}.xlsx"'},
        )
    elif fmt_lower == "pdf":
        pdf_buf = export_table_to_pdf(report_title, headers, rows, date_info=date_info)
        return StreamingResponse(
            pdf_buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{full_filename_base}.pdf"'},
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{fmt}'. Choose from 'csv', 'xlsx', 'pdf', or 'json'.")


# -------------------------------------------------------------
# 1. Executive Dashboard Aggregated Analytics
# -------------------------------------------------------------

@router.get(
    "/analytics/dashboard-summary",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN, UserRole.PRODUCTION]))],
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executive Dashboard summary metrics, KPIs, and operational aggregates."""
    return get_dashboard_analytics_summary(db, current_user=current_user)


# -------------------------------------------------------------
# 2. GSTR-1 Sales Register
# -------------------------------------------------------------

@router.get(
    "/reports/gstr1",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN]))],
)
@router.get(
    "/reports/gstr1/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN]))],
)
def export_gstr1(
    format: Optional[str] = Query("json", description="csv, xlsx, pdf, or json"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """GSTR-1 Outward Supplies / Sales Register."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")
    headers, rows = build_gstr1_sales_register(db, from_date, to_date)
    return format_report_response(
        "GSTR-1 Outward Supplies Register", headers, rows, format, "GSTR1_Sales_Register",
        from_date=from_date, to_date=to_date
    )


# -------------------------------------------------------------
# 3. GSTR-2 Purchase Register
# -------------------------------------------------------------

@router.get(
    "/reports/purchase-register",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
@router.get(
    "/reports/purchase-register/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
@router.get(
    "/reports/gstr2",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
@router.get(
    "/reports/gstr2/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def export_purchase_register(
    format: Optional[str] = Query("json", description="csv, xlsx, pdf, or json"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """GSTR-2 Inward Supplies / Purchase Register (Internal Procurement Register)."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")
    headers, rows = build_gstr2_purchase_register(db, from_date, to_date)
    return format_report_response(
        "GSTR-2 Purchase & Input Tax Register", headers, rows, format, "GSTR2_Purchase_Register",
        from_date=from_date, to_date=to_date
    )


# -------------------------------------------------------------
# 4. Stock Movement Ledger Register
# -------------------------------------------------------------

@router.get(
    "/reports/stock-movements",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
@router.get(
    "/reports/stock-movements/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
@router.get(
    "/reports/stock-ledger",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
@router.get(
    "/reports/stock-ledger/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
def export_stock_movements(
    format: Optional[str] = Query("json", description="csv, xlsx, pdf, or json"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    as_of_date: Optional[date] = Query(None),
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db),
):
    """Stock Movement Ledger Register."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")
    headers, rows = build_stock_ledger_report(db, from_date, to_date, as_of_date, limit)
    return format_report_response(
        "Stock Movement Ledger Register", headers, rows, format, "Stock_Movement_Ledger",
        from_date=from_date, to_date=to_date, as_of_date=as_of_date
    )


# -------------------------------------------------------------
# 5. Production Yield Variance Report
# -------------------------------------------------------------

@router.get(
    "/reports/production-variance",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
@router.get(
    "/reports/production-variance/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
@router.get(
    "/reports/production-yield",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
@router.get(
    "/reports/production-yield/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.PRODUCTION]))],
)
def export_production_variance(
    format: Optional[str] = Query("json", description="csv, xlsx, pdf, or json"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Production & Yield Variance Report."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")
    headers, rows = build_production_yield_report(db, from_date, to_date)
    return format_report_response(
        "Production & Yield Variance Report", headers, rows, format, "Production_Yield_Report",
        from_date=from_date, to_date=to_date
    )


# -------------------------------------------------------------
# 6. Receivables Ageing Schedule Report
# -------------------------------------------------------------

@router.get(
    "/reports/receivables-ageing",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN]))],
)
@router.get(
    "/reports/receivables-ageing/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN]))],
)
def export_receivables_ageing(
    format: Optional[str] = Query("json", description="csv, xlsx, pdf, or json"),
    as_of_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Accounts Receivable Ageing Schedule Report."""
    headers, rows = build_receivables_ageing_export_report(db, as_of_date)
    return format_report_response(
        "Accounts Receivable Ageing Report", headers, rows, format, "Receivables_Ageing",
        as_of_date=as_of_date
    )


# -------------------------------------------------------------
# 7. Financial Trial Balance Report
# -------------------------------------------------------------

@router.get(
    "/reports/trial-balance",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
@router.get(
    "/reports/trial-balance/export",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def export_trial_balance(
    format: Optional[str] = Query("json", description="csv, xlsx, pdf, or json"),
    as_of_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Trial Balance Statement Report."""
    headers, rows = build_trial_balance_export_report(db, as_of_date)
    return format_report_response(
        "Financial Trial Balance", headers, rows, format, "Trial_Balance",
        as_of_date=as_of_date
    )
