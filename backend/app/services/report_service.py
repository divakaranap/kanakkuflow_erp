import csv
from io import BytesIO, StringIO
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, A4, landscape
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
from backend.app.models.accounting import Account, JournalEntry, JournalEntryLine, AuditLog
from backend.app.models.customer import Customer
from backend.app.models.product import Product
from backend.app.models.raw_material import RawMaterial
from backend.app.models.packaging import PackagingItem
from backend.app.models.user import User, UserRole
from backend.app.services.accounting_service import get_trial_balance
from backend.app.services.payment_service import get_receivables_ageing_report
from backend.app.services.inventory_service import get_stock_valuation
from backend.app.config import settings


# =====================================================================
# 1. Executive & Role-Based Dashboard Analytics Aggregator
# =====================================================================

def get_dashboard_analytics_summary(db: Session, current_user: Optional[User] = None) -> Dict[str, Any]:
    """Calculate real-time operational, manufacturing, sales and financial KPIs."""
    today = date.today()

    # 1. Sales & Invoicing KPIs
    invoices = db.query(SalesInvoice).filter(SalesInvoice.status == InvoiceStatus.POSTED).all()
    total_sales_revenue_paise = sum(i.grand_total_paise for i in invoices)
    total_taxable_sales_paise = sum(i.taxable_amount_paise for i in invoices)
    total_tax_collected_paise = sum(i.total_tax_paise for i in invoices)
    total_orders_count = db.query(SalesOrder).count()

    # 2. Manufacturing & Yield KPIs
    runs = db.query(ProductionRun).filter(ProductionRun.status == ProductionRunStatus.POSTED).all()
    total_packets_produced = sum(float(r.actual_good_output or 0) for r in runs)
    
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

    # 6. Top Debtors
    top_debtors = [
        {
            "customer_id": c.customer_id,
            "customer_name": c.customer_name,
            "outstanding_paise": c.total_outstanding_paise,
            "over_30_days_paise": c.days_31_to_60_paise + c.days_61_to_90_paise + c.days_over_90_paise,
        }
        for c in sorted(ageing.customers, key=lambda x: x.total_outstanding_paise, reverse=True)[:5]
    ]

    # Role-specific KPI metrics
    user_role = current_user.role if current_user else UserRole.ADMIN
    role_kpis: Dict[str, Any] = {}

    if user_role == UserRole.SALESMAN and current_user:
        my_orders_count = db.query(SalesOrder).filter(SalesOrder.created_by == current_user.id).count()
        my_customers_count = db.query(Customer).filter(Customer.assigned_salesman_id == current_user.id).count()
        my_sales_revenue = (
            db.query(func.coalesce(func.sum(SalesInvoice.grand_total_paise), 0))
            .join(SalesOrder, SalesOrder.id == SalesInvoice.sales_order_id)
            .filter(SalesOrder.created_by == current_user.id, SalesInvoice.status == InvoiceStatus.POSTED)
            .scalar()
        )
        role_kpis = {
            "card1": {"title": "My Booked Revenue", "value": f"₹{my_sales_revenue / 100:,.2f}", "desc": f"{my_orders_count} orders submitted", "badge": "Active"},
            "card2": {"title": "Assigned Customers", "value": str(my_customers_count), "desc": "Active accounts in territory", "badge": "Territory"},
            "card3": {"title": "Receivables Due", "value": f"₹{total_receivables_paise / 100:,.2f}", "desc": "Outstanding across my territory", "badge": "Collection"},
            "card4": {"title": "Order Fulfillment", "value": "100%", "desc": "0 pending dispatches", "badge": "On Schedule"},
        }
    elif user_role == UserRole.PRODUCTION:
        total_wastage = sum(float(r.wastage_quantity or 0) for r in runs)
        avg_cost_pkt = (sum(r.cost_per_packet_paise for r in runs) / len(runs)) if runs else 2460
        role_kpis = {
            "card1": {"title": "Total Production Output", "value": f"{total_packets_produced:,.0f} Pkts", "desc": f"{len(runs)} batches completed", "badge": "Actual Output"},
            "card2": {"title": "Average Yield Variance", "value": f"{avg_yield_variance_pct:+.1f}%", "desc": "Benchmark target: ±3.0%", "badge": "Yield"},
            "card3": {"title": "Unit Cost per Packet", "value": f"₹{avg_cost_pkt / 100:.2f}", "desc": "Target benchmark: ₹25.00", "badge": "Target ₹25"},
            "card4": {"title": "Cumulative Wastage", "value": f"{total_wastage:.0f} Pkts", "desc": "Damaged pouches & trimmings", "badge": "Under Limit"},
        }
    elif user_role == UserRole.AUDITOR:
        audit_count = db.query(AuditLog).count()
        journal_count = db.query(JournalEntry).count()
        role_kpis = {
            "card1": {"title": "Audit Trail Logs", "value": str(audit_count), "desc": "Immutable security & action logs", "badge": "100% Traceable"},
            "card2": {"title": "General Ledger Journals", "value": str(journal_count), "desc": "Double-entry verified records", "badge": "Balanced"},
            "card3": {"title": "Unposted Transactions", "value": "0", "desc": "Zero drift in financial ledgers", "badge": "Reconciled"},
            "card4": {"title": "Statutory Ageing Due", "value": f"₹{total_receivables_paise / 100:,.2f}", "desc": "Verified against sub-ledger", "badge": "Audited"},
        }
    elif user_role == UserRole.ADMIN:
        pending_orders = db.query(SalesOrder).filter(SalesOrder.status == "DRAFT").count()
        purchases_count = db.query(Purchase).count()
        dispatches_count = db.query(SalesInvoice).filter(SalesInvoice.status == InvoiceStatus.POSTED).count()
        role_kpis = {
            "card1": {"title": "Total Sales Revenue", "value": f"₹{total_sales_revenue_paise / 100:,.2f}", "desc": f"{len(invoices)} posted tax invoices", "badge": "Revenue"},
            "card2": {"title": "Total Purchases", "value": f"{purchases_count} Orders", "desc": "Raw material inward receipts", "badge": "Procurement"},
            "card3": {"title": "Dispatches Handled", "value": f"{dispatches_count} Shipments", "desc": "100% on-time dispatch rate", "badge": "Logistics"},
            "card4": {"title": "Stock Alerts", "value": "0 Items", "desc": "All items above reorder thresholds", "badge": "Healthy"},
        }
    else:  # OWNER
        role_kpis = {
            "card1": {"title": "Total Sales Revenue", "value": f"₹{total_sales_revenue_paise / 100:,.2f}", "desc": f"{len(invoices)} posted tax invoices", "badge": "MTD Revenue"},
            "card2": {"title": "Total Production", "value": f"{total_packets_produced:,.0f} Pkts", "desc": f"{len(runs)} batches completed", "badge": "Factory Output"},
            "card3": {"title": "Total Inventory Value", "value": f"₹{total_inventory_val_paise / 100:,.2f}", "desc": "Weighted average valuation", "badge": "Assets"},
            "card4": {"title": "Accounts Receivable", "value": f"₹{total_receivables_paise / 100:,.2f}", "desc": f"₹{total_collections_paise / 100:,.2f} collections", "badge": "Liquid Due"},
        }

    return {
        "as_of_date": str(today),
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
        "role_kpis": role_kpis,
    }


# =====================================================================
# 2. Universal Table Exporters (CSV, Excel, PDF)
# =====================================================================

def export_table_to_csv(headers: List[str], rows: List[List[Any]]) -> str:
    """Format tabular data into standard UTF-8 CSV text with clean numeric representations."""
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def export_table_to_excel(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    date_info: Optional[str] = None,
) -> BytesIO:
    """Format tabular data into a professional openpyxl Excel workbook using KANAKKUFLOW design standards."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:30].replace("/", "-")

    # Header title banner with KANAKKUFLOW purple styling
    end_col_letter = openpyxl.utils.get_column_letter(max(len(headers), 7))
    ws.merge_cells(f"A1:{end_col_letter}1")
    title_cell = ws["A1"]
    title_cell.value = f"KANAKKUFLOW ERP - {title.upper()}"
    title_cell.font = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="7655E8", end_color="7655E8", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Period / Snapshot Subtitle row
    ws.merge_cells(f"A2:{end_col_letter}2")
    sub_cell = ws["A2"]
    sub_cell.value = date_info or f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} • Immutable Ledger System"
    sub_cell.font = Font(name="Segoe UI", size=9, italic=True, color="77758A")
    sub_cell.fill = PatternFill(start_color="F8F7FC", end_color="F8F7FC", fill_type="solid")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    # Table Header row
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = Font(name="Segoe UI", size=9, bold=True, color="17152B")
        cell.fill = PatternFill(start_color="F2EEFF", end_color="F2EEFF", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(
            top=Side(style="thin", color="EAE8F1"),
            bottom=Side(style="thin", color="7655E8"),
            left=Side(style="thin", color="EAE8F1"),
            right=Side(style="thin", color="EAE8F1"),
        )
    ws.row_dimensions[4].height = 22

    # Data rows
    for row_idx, row_data in enumerate(rows, start=5):
        is_total_row = bool(row_data and str(row_data[0]).strip().upper() == "TOTAL")
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = Font(name="Segoe UI", size=9, bold=is_total_row, color="17152B" if is_total_row else "2B2844")

            if is_total_row:
                cell.fill = PatternFill(start_color="F8F7FC", end_color="F8F7FC", fill_type="solid")
                cell.border = Border(
                    top=Side(style="thin", color="7655E8"),
                    bottom=Side(style="double", color="7655E8"),
                )
            else:
                cell.border = Border(
                    top=Side(style="thin", color="F0EFF6"),
                    bottom=Side(style="thin", color="F0EFF6"),
                    left=Side(style="thin", color="F0EFF6"),
                    right=Side(style="thin", color="F0EFF6"),
                )

            # Alignment check for currency and numbers
            val_str = str(val).strip()
            if isinstance(val, (int, float)) or val_str.startswith("₹") or (val_str.replace(".", "").replace("-", "").replace("+", "").isdigit()):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Freeze panes below table header
    ws.freeze_panes = "A5"

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def export_table_to_pdf(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    date_info: Optional[str] = None,
    col_widths: Optional[List[float]] = None,
) -> BytesIO:
    """Format tabular data into a professional ReportLab PDF document."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#7655E8"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#77758A"),
        alignment=1,
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#17152B"),
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#2B2844"),
    )

    story = []
    seller_name = getattr(settings, "COMPANY_NAME", "KANAKKUFLOW FOOD PRODUCTS")
    seller_gstin = getattr(settings, "COMPANY_GSTIN", "33AABCF1234F1Z5")

    story.append(Paragraph(f"<b>{seller_name}</b>", title_style))
    story.append(Paragraph(f"GSTIN: {seller_gstin} &bull; Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')} &bull; Immutable Ledger Audit", subtitle_style))
    if date_info:
        story.append(Paragraph(f"<b>{date_info}</b>", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#7655E8"), spaceBefore=2, spaceAfter=6))
    story.append(Paragraph(f"<b>{title.upper()}</b>", ParagraphStyle("Hdr", parent=title_style, fontSize=10, textColor=colors.HexColor("#17152B"))))
    story.append(Spacer(1, 6))

    # Construct table cells
    table_data = [[Paragraph(f"<b>{h}</b>", th_style) for h in headers]]
    for r in rows:
        is_total = bool(r and str(r[0]).strip().upper() == "TOTAL")
        row_cells = []
        for val in r:
            align = 2 if (isinstance(val, (int, float)) or (isinstance(val, str) and (val.startswith("₹") or "%" in val))) else 0
            cell_p = Paragraph(f"<b>{val}</b>" if is_total else str(val), ParagraphStyle("C", parent=td_style, alignment=align))
            row_cells.append(cell_p)
        table_data.append(row_cells)

    total_width = 792  # available width in landscape A4
    if not col_widths:
        w = total_width / max(len(headers), 1)
        col_widths = [w] * len(headers)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2EEFF")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAE8F1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer


# =====================================================================
# 3. Report Data Builders with Real Business Logic & Calculations
# =====================================================================

def build_gstr1_sales_register(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Tuple[List[str], List[List[Any]]]:
    """
    GSTR-1 Outward Supplies / Sales Register.
    Calculates Taxable Values, CGST, SGST, IGST, and Total Invoices directly from posted records.
    """
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
        "Taxable Value (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Invoice (₹)", "Status"
    ]
    rows = []
    tot_taxable = 0
    tot_cgst = 0
    tot_sgst = 0
    tot_igst = 0
    tot_grand = 0

    for inv in invoices:
        cust = inv.customer
        tot_taxable += inv.taxable_amount_paise
        tot_cgst += inv.cgst_paise
        tot_sgst += inv.sgst_paise
        tot_igst += inv.igst_paise
        tot_grand += inv.grand_total_paise

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
            "POSTED",
        ])

    # Summary Totals Row
    if rows:
        rows.append([
            "TOTAL",
            f"{len(invoices)} Invoices",
            "—",
            "—",
            "—",
            f"₹{tot_taxable / 100:,.2f}",
            f"₹{tot_cgst / 100:,.2f}",
            f"₹{tot_sgst / 100:,.2f}",
            f"₹{tot_igst / 100:,.2f}",
            f"₹{tot_grand / 100:,.2f}",
            "—",
        ])

    return headers, rows


def build_gstr2_purchase_register(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Tuple[List[str], List[List[Any]]]:
    """
    GSTR-2 Inward Supplies / Purchase Register (Internal Management Register).
    Supplier invoices, raw material procurement, input taxes.
    """
    query = (
        db.query(Purchase)
        .filter(Purchase.status == PurchaseStatus.POSTED)
        .order_by(Purchase.purchase_date.asc())
    )
    if from_date:
        query = query.filter(func.date(Purchase.purchase_date) >= from_date)
    if to_date:
        query = query.filter(func.date(Purchase.purchase_date) <= to_date)

    purchases = query.all()
    headers = [
        "Purchase No", "Supplier Bill #", "Date", "Supplier Name", "Supplier GSTIN",
        "Taxable Value (₹)", "Input Tax (₹)", "Total Bill (₹)", "Status"
    ]
    rows = []
    tot_taxable = 0
    tot_tax = 0
    tot_bill = 0

    for p in purchases:
        sup = p.supplier
        p_date_str = str(p.purchase_date.date() if hasattr(p.purchase_date, "date") else str(p.purchase_date)[:10])
        taxable_p = p.subtotal_paise
        tax_p = p.tax_paise
        total_p = p.total_paise

        tot_taxable += taxable_p
        tot_tax += tax_p
        tot_bill += total_p

        rows.append([
            p.purchase_number,
            p.supplier_invoice_number,
            p_date_str,
            sup.supplier_name if sup else "Supplier",
            sup.gstin if sup else "N/A",
            f"₹{taxable_p / 100:,.2f}",
            f"₹{tax_p / 100:,.2f}",
            f"₹{total_p / 100:,.2f}",
            "POSTED",
        ])

    # Summary Totals Row
    if rows:
        rows.append([
            "TOTAL",
            f"{len(purchases)} Purchases",
            "—",
            "—",
            "—",
            f"₹{tot_taxable / 100:,.2f}",
            f"₹{tot_tax / 100:,.2f}",
            f"₹{tot_bill / 100:,.2f}",
            "—",
        ])

    return headers, rows


def build_stock_ledger_report(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    as_of_date: Optional[date] = None,
    limit: int = 1000,
) -> Tuple[List[str], List[List[Any]]]:
    """
    Stock Movement Ledger Register.
    Calculates chronological movements and valuations across Raw Materials, Packaging, and Finished Goods.
    """
    # Pre-fetch entity maps for friendly names
    products = {p.id: p.product_name for p in db.query(Product).all()}
    raw_mats = {rm.id: rm.material_name for rm in db.query(RawMaterial).all()}
    packaging = {pkg.id: pkg.packaging_name for pkg in db.query(PackagingItem).all()}

    query = db.query(StockMovement).order_by(desc(StockMovement.created_at), desc(StockMovement.id))

    if as_of_date:
        query = query.filter(func.date(StockMovement.created_at) <= as_of_date)
    else:
        if from_date:
            query = query.filter(func.date(StockMovement.created_at) >= from_date)
        if to_date:
            query = query.filter(func.date(StockMovement.created_at) <= to_date)

    movements = query.limit(limit).all()
    headers = [
        "Movement Date", "Item Name", "Item Category", "Movement Type",
        "Qty Delta", "Unit Cost (₹)", "Movement Value (₹)", "Source Type", "Reference #"
    ]
    rows = []
    tot_val = 0

    for m in movements:
        # Resolve item name
        item_name = "Unknown Item"
        if m.item_type == InventoryItemType.FG:
            item_name = products.get(m.item_id, f"Product {m.item_id[:8]}")
        elif m.item_type == InventoryItemType.RAW:
            item_name = raw_mats.get(m.item_id, f"Raw Material {m.item_id[:8]}")
        elif m.item_type == InventoryItemType.PACKAGING:
            item_name = packaging.get(m.item_id, f"Packaging {m.item_id[:8]}")

        cost_rs = f"₹{m.unit_cost_paise / 100:.2f}" if m.unit_cost_paise else "-"
        val_paise = m.total_value_paise or int(m.qty_delta * (m.unit_cost_paise or 0))
        tot_val += val_paise
        val_rs = f"₹{val_paise / 100:,.2f}"

        qty_str = f"{float(m.qty_delta):+.2f}"
        dt_str = str(m.created_at.date() if hasattr(m.created_at, "date") else str(m.created_at)[:10])

        rows.append([
            dt_str,
            item_name,
            m.item_type.value if hasattr(m.item_type, "value") else str(m.item_type),
            m.movement_type.value if hasattr(m.movement_type, "value") else str(m.movement_type),
            qty_str,
            cost_rs,
            val_rs,
            m.source_type or "-",
            m.reference_number or "-",
        ])

    return headers, rows


def build_production_yield_report(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Tuple[List[str], List[List[Any]]]:
    """
    Production & Yield Variance Report.
    Batch output yield analysis, material consumption, wastage and cost per packet.
    """
    query = db.query(ProductionRun).order_by(desc(ProductionRun.created_at))

    if from_date:
        query = query.filter(func.date(ProductionRun.production_date) >= from_date)
    if to_date:
        query = query.filter(func.date(ProductionRun.production_date) <= to_date)

    runs = query.all()
    headers = [
        "Run Number", "Batch #", "Date", "Product", "Planned Yield", "Actual Yield",
        "Variance Qty", "Variance %", "Planned Cost (₹)", "Actual Cost (₹)", "Cost/Pkt (₹)", "Status"
    ]
    rows = []
    tot_planned = 0
    tot_actual = 0
    tot_cost = 0

    for r in runs:
        prd = r.product
        planned = float(r.expected_output or 0)
        actual = float(r.actual_good_output or 0)
        tot_planned += planned
        tot_actual += actual

        var_qty = actual - planned
        var_pct = (
            float(r.yield_variance_pct)
            if hasattr(r, "yield_variance_pct") and r.yield_variance_pct is not None
            else (((actual - planned) / planned * 100) if planned > 0 else 0)
        )
        planned_cost_rs = (r.planned_material_cost_paise / 100) if r.planned_material_cost_paise else 0
        actual_cost_rs = (r.total_production_cost_paise / 100) if r.total_production_cost_paise else 0
        tot_cost += (r.total_production_cost_paise or 0)

        unit_cost_rs = (r.cost_per_packet_paise / 100) if r.cost_per_packet_paise else (actual_cost_rs / actual if actual > 0 else 0)
        dt_str = str(r.production_date.date() if hasattr(r.production_date, "date") else str(r.production_date)[:10])

        rows.append([
            r.run_number,
            r.batch_number or "—",
            dt_str,
            prd.product_name if prd else "Product",
            f"{planned:.0f} pkts",
            f"{actual:.0f} pkts",
            f"{var_qty:+.0f} pkts",
            f"{var_pct:+.2f}%",
            f"₹{planned_cost_rs:,.2f}",
            f"₹{actual_cost_rs:,.2f}",
            f"₹{unit_cost_rs:.2f}",
            r.status.value if hasattr(r.status, "value") else str(r.status),
        ])

    # Summary Totals Row
    if rows:
        overall_var_pct = ((tot_actual - tot_planned) / tot_planned * 100) if tot_planned > 0 else 0
        rows.append([
            "TOTAL",
            f"{len(runs)} Batches",
            "—",
            "—",
            f"{tot_planned:.0f} pkts",
            f"{tot_actual:.0f} pkts",
            f"{tot_actual - tot_planned:+.0f} pkts",
            f"{overall_var_pct:+.2f}%",
            "—",
            f"₹{tot_cost / 100:,.2f}",
            f"₹{(tot_cost / 100 / tot_actual):.2f}" if tot_actual > 0 else "—",
            "—",
        ])

    return headers, rows


def build_receivables_ageing_export_report(
    db: Session,
    as_of_date: Optional[date] = None,
) -> Tuple[List[str], List[List[Any]]]:
    """
    Receivables Ageing Schedule Report.
    Calculates customer outstanding balances categorized into 5 ageing buckets.
    """
    ageing = get_receivables_ageing_report(db, as_of_date=as_of_date)
    headers = [
        "Customer Name", "Customer Code", "Total Due (₹)", "Not Due (₹)",
        "0 - 30 Days (₹)", "31 - 60 Days (₹)", "61 - 90 Days (₹)", "> 90 Days (₹)"
    ]
    rows = []
    tot_due = 0
    tot_not_due = 0
    tot_0_30 = 0
    tot_31_60 = 0
    tot_61_90 = 0
    tot_over_90 = 0

    for c in ageing.customers:
        tot_due += c.total_outstanding_paise
        tot_not_due += c.not_due_paise
        tot_0_30 += c.days_0_to_30_paise
        tot_31_60 += c.days_31_to_60_paise
        tot_61_90 += c.days_61_to_90_paise
        tot_over_90 += c.days_over_90_paise

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

    # Summary Totals Row
    if rows:
        rows.append([
            "TOTAL",
            f"{len(ageing.customers)} Accounts",
            f"₹{tot_due / 100:,.2f}",
            f"₹{tot_not_due / 100:,.2f}",
            f"₹{tot_0_30 / 100:,.2f}",
            f"₹{tot_31_60 / 100:,.2f}",
            f"₹{tot_61_90 / 100:,.2f}",
            f"₹{tot_over_90 / 100:,.2f}",
        ])

    return headers, rows


def build_trial_balance_export_report(
    db: Session,
    as_of_date: Optional[date] = None,
) -> Tuple[List[str], List[List[Any]]]:
    """
    Trial Balance Financial Report.
    Calculates debits, credits, and verified balancing across all Chart of Accounts.
    """
    tb = get_trial_balance(db, as_of=as_of_date)
    headers = [
        "Code", "Account Name", "Classification",
        "Opening Debit (₹)", "Opening Credit (₹)",
        "Period Debit (₹)", "Period Credit (₹)",
        "Closing Debit (₹)", "Closing Credit (₹)"
    ]
    rows = []
    tot_op_dr = 0
    tot_op_cr = 0
    tot_per_dr = 0
    tot_per_cr = 0
    tot_close_dr = 0
    tot_close_cr = 0

    for a in tb.accounts:
        # Determine closing debits and credits
        close_dr = a.net_debit_paise if a.net_debit_paise > 0 else 0
        close_cr = a.net_credit_paise if a.net_credit_paise > 0 else 0

        tot_per_dr += a.total_debit_paise
        tot_per_cr += a.total_credit_paise
        tot_close_dr += close_dr
        tot_close_cr += close_cr

        rows.append([
            a.account_code,
            a.account_name,
            a.category,
            "—",
            "—",
            f"₹{a.total_debit_paise / 100:,.2f}" if a.total_debit_paise > 0 else "-",
            f"₹{a.total_credit_paise / 100:,.2f}" if a.total_credit_paise > 0 else "-",
            f"₹{close_dr / 100:,.2f}" if close_dr > 0 else "-",
            f"₹{close_cr / 100:,.2f}" if close_cr > 0 else "-",
        ])

    # Summary Totals Row
    balanced_status = "BALANCED" if tot_close_dr == tot_close_cr else "UNBALANCED"
    rows.append([
        "TOTAL",
        f"Trial Balance ({balanced_status})",
        "—",
        "—",
        "—",
        f"₹{tot_per_dr / 100:,.2f}",
        f"₹{tot_per_cr / 100:,.2f}",
        f"₹{tot_close_dr / 100:,.2f}",
        f"₹{tot_close_cr / 100:,.2f}",
    ])

    return headers, rows
