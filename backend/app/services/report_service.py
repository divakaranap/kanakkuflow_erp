import csv
from io import BytesIO, StringIO
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.app.models.sales import SalesInvoice, SalesInvoiceItem, InvoiceStatus, SalesOrder
from backend.app.models.purchase import Purchase, PurchaseLine, PurchaseStatus
from backend.app.models.inventory import StockMovement, InventoryBalance, InventoryItemType
from backend.app.models.production import ProductionRun, ProductionRunStatus
from backend.app.models.payment import CustomerPayment
from backend.app.models.accounting import Account, JournalEntry, JournalEntryLine
from backend.app.models.customer import Customer
from backend.app.models.product import Product
from backend.app.services.accounting_service import get_trial_balance
from backend.app.services.payment_service import get_receivables_ageing_report
from backend.app.services.inventory_service import get_stock_valuation
from backend.app.config import settings


# 1. Executive Dashboard Aggregator

def get_dashboard_analytics_summary(db: Session) -> Dict[str, Any]:
    """Calculate real-time operational, manufacturing, sales and financial KPIs."""
    # 1. Sales & Invoicing KPIs
    invoices = db.query(SalesInvoice).filter(SalesInvoice.status == InvoiceStatus.POSTED).all()
    total_sales_revenue_paise = sum(i.grand_total_paise for i in invoices)
    total_taxable_sales_paise = sum(i.taxable_amount_paise for i in invoices)
    total_tax_collected_paise = sum(i.total_tax_paise for i in invoices)
    total_orders_count = db.query(SalesOrder).count()

    # 2. Manufacturing & Yield KPIs
    runs = db.query(ProductionRun).filter(ProductionRun.status == ProductionRunStatus.POSTED).all()
    total_packets_produced = sum(float(r.actual_good_output or 0) for r in runs)
    
    # Calculate weighted average yield variance %
    tot_planned_yield = sum(float(r.expected_output or 0) for r in runs)
    tot_actual_yield = sum(float(r.actual_good_output or 0) for r in runs)
    avg_yield_variance_pct = (
        ((tot_actual_yield - tot_planned_yield) / tot_planned_yield * 100)
        if tot_planned_yield > 0
        else 0.0
    )

    # 3. Inventory Valuation
    valuation = get_stock_valuation(db)
    total_inventory_val_paise = valuation.total_valuation_paise
    rm_val_paise = valuation.raw_materials_valuation_paise
    pkg_val_paise = valuation.packaging_valuation_paise
    fg_val_paise = valuation.finished_goods_valuation_paise

    # 4. Receivables & Collections
    ageing = get_receivables_ageing_report(db)
    total_receivables_paise = ageing.total_receivables_paise
    total_collections_paise = db.query(func.coalesce(func.sum(CustomerPayment.amount_paise), 0)).scalar()

    # 5. Top Products by Revenue
    top_products_data = (
        db.query(
            SalesInvoiceItem.product_name,
            func.sum(SalesInvoiceItem.quantity).label("total_qty"),
            func.sum(SalesInvoiceItem.line_total_paise).label("total_revenue"),
        )
        .join(SalesInvoice, SalesInvoice.id == SalesInvoiceItem.invoice_id)
        .filter(SalesInvoice.status == InvoiceStatus.POSTED)
        .group_by(SalesInvoiceItem.product_name)
        .order_by(desc("total_revenue"))
        .limit(5)
        .all()
    )

    top_products = [
        {
            "product_name": r.product_name,
            "total_quantity": float(r.total_qty),
            "total_revenue_paise": int(r.total_revenue),
        }
        for r in top_products_data
    ]

    # 6. Top Customers by Outstanding Receivables
    top_debtors = [
        {
            "customer_id": c.customer_id,
            "customer_name": c.customer_name,
            "outstanding_paise": c.total_outstanding_paise,
            "over_30_days_paise": c.days_31_to_60_paise + c.days_61_to_90_paise + c.days_over_90_paise,
        }
        for c in sorted(ageing.customers, key=lambda x: x.total_outstanding_paise, reverse=True)[:5]
    ]

    return {
        "as_of_date": str(date.today()),
        "sales": {
            "total_revenue_paise": total_sales_revenue_paise,
            "total_taxable_paise": total_taxable_sales_paise,
            "total_tax_paise": total_tax_collected_paise,
            "invoices_count": len(invoices),
            "orders_count": total_orders_count,
        },
        "production": {
            "total_packets_produced": total_packets_produced,
            "completed_runs_count": len(runs),
            "avg_yield_variance_pct": round(avg_yield_variance_pct, 2),
        },
        "inventory": {
            "total_valuation_paise": total_inventory_val_paise,
            "raw_materials_paise": rm_val_paise,
            "packaging_paise": pkg_val_paise,
            "finished_goods_paise": fg_val_paise,
        },
        "finance": {
            "total_receivables_paise": total_receivables_paise,
            "total_collections_paise": total_collections_paise,
            "over_30_days_paise": ageing.total_31_to_60_paise + ageing.total_61_to_90_paise + ageing.total_over_90_paise,
        },
        "top_products": top_products,
        "top_debtors": top_debtors,
    }


# 2. Universal Table Exporters (CSV, Excel, PDF)

def export_table_to_csv(headers: List[str], rows: List[List[Any]]) -> str:
    """Format tabular data into standard CSV text."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def export_table_to_excel(title: str, headers: List[str], rows: List[List[Any]]) -> BytesIO:
    """Format tabular data into a styled Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:30]

    # Header title banner
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = f"FACTORYFLOW ERP - {title.upper()}"
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Table Header row
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx)
        cell.value = header
        cell.font = Font(name="Calibri", size=10, bold=True, color="0F172A")
        cell.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
        )
    ws.row_dimensions[3].height = 20

    # Data rows
    for row_idx, row_data in enumerate(rows, start=4):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = Font(name="Calibri", size=9)
            cell.border = Border(
                top=Side(style="thin", color="E2E8F0"),
                bottom=Side(style="thin", color="E2E8F0"),
                left=Side(style="thin", color="E2E8F0"),
                right=Side(style="thin", color="E2E8F0"),
            )
            # Alignment check for numbers
            if isinstance(val, (int, float)) or (isinstance(val, str) and (val.startswith("₹") or val.replace(".", "").isdigit())):
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="left")

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def export_table_to_pdf(title: str, headers: List[str], rows: List[List[Any]], col_widths: Optional[List[float]] = None) -> BytesIO:
    """Format tabular data into a professional ReportLab PDF document."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []
    seller_name = getattr(settings, "COMPANY_NAME", "FACTORYFLOW FOOD PRODUCTS")
    seller_gstin = getattr(settings, "COMPANY_GSTIN", "33AABCF1234F1Z5")

    story.append(Paragraph(f"<b>{seller_name}</b>", title_style))
    story.append(Paragraph(f"GSTIN: {seller_gstin} &bull; Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f172a"), spaceBefore=2, spaceAfter=6))
    story.append(Paragraph(f"<b>{title.upper()}</b>", ParagraphStyle("Hdr", parent=title_style, fontSize=11, textColor=colors.HexColor("#1e3a8a"))))
    story.append(Spacer(1, 8))

    # Construct table cells
    table_data = [[Paragraph(f"<b>{h}</b>", th_style) for h in headers]]
    for r in rows:
        row_cells = []
        for val in r:
            align = 2 if (isinstance(val, (int, float)) or (isinstance(val, str) and val.startswith("₹"))) else 0
            row_cells.append(Paragraph(str(val), ParagraphStyle("C", parent=td_style, alignment=align)))
        table_data.append(row_cells)

    total_width = 535
    if not col_widths:
        w = total_width / len(headers)
        col_widths = [w] * len(headers)

    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer


# 3. Report Data Builders

def build_gstr1_sales_register(db: Session, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Tuple[List[str], List[List[Any]]]:
    """GSTR-1 Outward Supplies / Sales Register."""
    query = (
        db.query(SalesInvoice)
        .filter(SalesInvoice.status == InvoiceStatus.POSTED)
        .order_by(SalesInvoice.invoice_date.asc())
    )
    if from_date:
        query = query.filter(SalesInvoice.invoice_date >= from_date)
    if to_date:
        query = query.filter(SalesInvoice.invoice_date <= to_date)

    invoices = query.all()
    headers = [
        "Invoice No", "Date", "Customer Name", "Customer GSTIN", "Place of Supply",
        "Taxable Value (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Invoice (₹)"
    ]
    rows = []
    for inv in invoices:
        cust = inv.customer
        rows.append([
            inv.invoice_number,
            str(inv.invoice_date),
            cust.customer_name if cust else "Direct",
            inv.buyer_gstin or "Unregistered",
            inv.place_of_supply_state_code,
            f"₹{inv.taxable_amount_paise / 100:,.2f}",
            f"₹{inv.cgst_paise / 100:,.2f}",
            f"₹{inv.sgst_paise / 100:,.2f}",
            f"₹{inv.igst_paise / 100:,.2f}",
            f"₹{inv.grand_total_paise / 100:,.2f}",
        ])
    return headers, rows


def build_gstr2_purchase_register(db: Session, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Tuple[List[str], List[List[Any]]]:
    """GSTR-2 Inward Supplies / Purchase Register."""
    query = (
        db.query(Purchase)
        .filter(Purchase.status == PurchaseStatus.POSTED)
        .order_by(Purchase.purchase_date.asc())
    )
    if from_date:
        query = query.filter(Purchase.purchase_date >= from_date)
    if to_date:
        query = query.filter(Purchase.purchase_date <= to_date)

    purchases = query.all()
    headers = [
        "Purchase No", "Date", "Supplier Name", "Supplier GSTIN",
        "Taxable Value (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Bill (₹)"
    ]
    rows = []
    for p in purchases:
        sup = p.supplier
        taxable = p.taxable_total_paise or p.subtotal_paise
        rows.append([
            p.purchase_number,
            str(p.purchase_date),
            sup.supplier_name if sup else "Supplier",
            sup.gstin if sup else "N/A",
            f"₹{taxable / 100:,.2f}",
            f"₹{(p.cgst_total_paise or 0) / 100:,.2f}",
            f"₹{(p.sgst_total_paise or 0) / 100:,.2f}",
            f"₹{(p.igst_total_paise or 0) / 100:,.2f}",
            f"₹{p.grand_total_paise / 100:,.2f}",
        ])
    return headers, rows


def build_stock_ledger_report(db: Session, limit: int = 500) -> Tuple[List[str], List[List[Any]]]:
    """Stock Movement Ledger Register."""
    movements = (
        db.query(StockMovement)
        .order_by(desc(StockMovement.created_at), desc(StockMovement.id))
        .limit(limit)
        .all()
    )
    headers = ["Movement Date", "Item Type", "Movement Type", "Qty Delta", "Unit Cost (₹)", "Source Document", "Reference #"]
    rows = []
    for m in movements:
        cost_rs = f"₹{m.unit_cost_paise / 100:.2f}" if m.unit_cost_paise else "-"
        qty_str = f"{float(m.qty_delta):+.2f}"
        dt_str = str(m.created_at.date() if hasattr(m.created_at, "date") else m.created_at)
        rows.append([
            dt_str,
            m.item_type.value if hasattr(m.item_type, "value") else str(m.item_type),
            m.movement_type.value if hasattr(m.movement_type, "value") else str(m.movement_type),
            qty_str,
            cost_rs,
            m.source_type or "-",
            m.reference_number or "-",
        ])
    return headers, rows


def build_production_yield_report(db: Session) -> Tuple[List[str], List[List[Any]]]:
    """Production & Yield Variance Report."""
    runs = (
        db.query(ProductionRun)
        .order_by(desc(ProductionRun.created_at))
        .all()
    )
    headers = [
        "Run Number", "Date", "Product", "Planned Yield", "Actual Yield",
        "Variance Qty", "Variance %", "Total Cost (₹)", "Cost/Pkt (₹)", "Status"
    ]
    rows = []
    for r in runs:
        prd = r.product
        planned = float(r.expected_output or 0)
        actual = float(r.actual_good_output or 0)
        var_qty = actual - planned
        var_pct = float(r.yield_variance_pct) if r.yield_variance_pct is not None else (((actual - planned) / planned * 100) if planned > 0 else 0)
        tot_cost_rs = (r.total_production_cost_paise / 100) if r.total_production_cost_paise else 0
        unit_cost_rs = (r.actual_unit_cost / 100) if r.actual_unit_cost else (tot_cost_rs / actual if actual > 0 else 0)
        dt_str = str(r.production_date.date() if hasattr(r.production_date, "date") else r.created_at.date() if hasattr(r.created_at, "date") else "-")

        rows.append([
            r.run_number,
            dt_str,
            prd.product_name if prd else "Product",
            f"{planned:.0f} pkts",
            f"{actual:.0f} pkts",
            f"{var_qty:+.0f} pkts",
            f"{var_pct:+.2f}%",
            f"₹{tot_cost_rs:,.2f}",
            f"₹{unit_cost_rs:.2f}",
            r.status.value if hasattr(r.status, "value") else str(r.status),
        ])
    return headers, rows


def build_receivables_ageing_export_report(db: Session) -> Tuple[List[str], List[List[Any]]]:
    """Receivables Ageing Schedule Report."""
    ageing = get_receivables_ageing_report(db)
    headers = ["Customer Name", "Customer Code", "Total Due (₹)", "Not Due (₹)", "0 - 30 Days (₹)", "31 - 60 Days (₹)", "61 - 90 Days (₹)", "> 90 Days (₹)"]
    rows = []
    for c in ageing.customers:
        rows.append([
            c.customer_name,
            c.customer_code or "-",
            f"₹{c.total_outstanding_paise / 100:,.2f}",
            f"₹{c.not_due_paise / 100:,.2f}",
            f"₹{c.days_0_to_30_paise / 100:,.2f}",
            f"₹{c.days_31_to_60_paise / 100:,.2f}",
            f"₹{c.days_61_to_90_paise / 100:,.2f}",
            f"₹{c.days_over_90_paise / 100:,.2f}",
        ])
    return headers, rows


def build_trial_balance_export_report(db: Session) -> Tuple[List[str], List[List[Any]]]:
    """Trial Balance Financial Report."""
    tb = get_trial_balance(db)
    headers = ["Code", "Account Name", "Category", "Gross Debit (₹)", "Gross Credit (₹)", "Net Debit (₹)", "Net Credit (₹)"]
    rows = []
    for a in tb.accounts:
        rows.append([
            a.account_code,
            a.account_name,
            a.category,
            f"₹{a.total_debit_paise / 100:,.2f}" if a.total_debit_paise > 0 else "-",
            f"₹{a.total_credit_paise / 100:,.2f}" if a.total_credit_paise > 0 else "-",
            f"₹{a.net_debit_paise / 100:,.2f}" if a.net_debit_paise > 0 else "-",
            f"₹{a.net_credit_paise / 100:,.2f}" if a.net_credit_paise > 0 else "-",
        ])
    return headers, rows
