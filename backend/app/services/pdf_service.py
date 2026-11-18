import os
from io import BytesIO
from decimal import Decimal
from typing import Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.app.config import settings

# Number to Indian Words converter
ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def number_to_indian_words(n: int) -> str:
    """Convert integer Rupees into Indian currency words format (Lakhs, Crores)."""
    if n == 0:
        return "Zero"

    def helper(num: int) -> str:
        if num < 20:
            return ONES[num]
        elif num < 100:
            return TENS[num // 10] + (" " + ONES[num % 10] if num % 10 != 0 else "")
        elif num < 1000:
            return ONES[num // 100] + " Hundred" + (" and " + helper(num % 100) if num % 100 != 0 else "")
        elif num < 100000:
            return helper(num // 1000) + " Thousand" + (" " + helper(num % 1000) if num % 1000 != 0 else "")
        elif num < 10000000:
            return helper(num // 100000) + " Lakh" + (" " + helper(num % 100000) if num % 100000 != 0 else "")
        else:
            return helper(num // 10000000) + " Crore" + (" " + helper(num % 10000000) if num % 10000000 != 0 else "")

    rupees = helper(n)
    return f"Indian Rupees {rupees} Only"


def generate_invoice_pdf_buffer(invoice: Any) -> BytesIO:
    """Generate a clean, professional GST Tax Invoice PDF using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"),
    )
    header_sub_style = ParagraphStyle(
        "HeaderSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    section_head_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
    )

    story = []

    # 1. Header: Seller Info & Tax Invoice Badge
    seller_name = getattr(settings, "SELLER_COMPANY_NAME", "KANAKKUFLOW FOODS PRIVATE LIMITED")
    seller_gstin = invoice.seller_gstin or getattr(settings, "SELLER_GSTIN", "33AAAAF1234A1Z5")
    seller_addr = getattr(settings, "SELLER_ADDRESS", "Plot 12, Food Processing SEZ, Thuvakudi, Tiruchirappalli, Tamil Nadu 620015")

    header_data = [
        [
            Paragraph(f"<b>{seller_name}</b><br/>{seller_addr}<br/><b>GSTIN:</b> {seller_gstin} | <b>State Code:</b> {invoice.place_of_supply_state_code[:2]}", header_sub_style),
            Paragraph("<font size=14 color='#1e3a8a'><b>TAX INVOICE</b></font><br/><font size=8 color='#64748b'>ORIGINAL FOR RECIPIENT</font>", ParagraphStyle("RightH", parent=header_sub_style, alignment=2)),
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 180])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=8))

    # 2. Invoice & Customer Meta
    cust = invoice.customer
    customer_name = cust.customer_name if cust else "Valued Customer"
    cust_addr = f"{cust.billing_address}, {cust.city}, {cust.state} - {cust.pincode}" if cust else ""
    cust_gstin = invoice.buyer_gstin or (cust.gstin if cust else "URP (Unregistered)")

    meta_data = [
        [
            Paragraph("<b>BILLED TO (BUYER):</b>", section_head_style),
            Paragraph("<b>INVOICE DETAILS:</b>", section_head_style),
        ],
        [
            Paragraph(f"<b>{customer_name}</b><br/>{cust_addr}<br/><b>GSTIN / UIN:</b> {cust_gstin}<br/><b>Place of Supply:</b> {invoice.place_of_supply_state_code}", body_style),
            Paragraph(f"<b>Invoice No:</b> {invoice.invoice_number}<br/><b>Invoice Date:</b> {invoice.invoice_date.strftime('%d-%b-%Y')}<br/><b>Order Ref:</b> {getattr(invoice.sales_order, 'order_number', 'N/A')}<br/><b>Status:</b> {invoice.status.value}", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[310, 210])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Items Table
    is_intra = (invoice.cgst_paise > 0 or invoice.sgst_paise > 0)
    if is_intra:
        item_headers = ["#", "Item Description", "HSN", "Qty", "Rate (₹)", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "Total (₹)"]
        col_widths = [20, 150, 45, 45, 50, 60, 50, 50, 50]
    else:
        item_headers = ["#", "Item Description", "HSN", "Qty", "Rate (₹)", "Taxable (₹)", "IGST (₹)", "Total (₹)"]
        col_widths = [20, 180, 50, 50, 55, 65, 50, 50]

    table_rows = [[Paragraph(f"<b>{h}</b>", table_cell_bold) for h in item_headers]]

    for idx, it in enumerate(invoice.items, start=1):
        rate_rs = f"{it.unit_price_paise / 100:.2f}"
        taxable_rs = f"{it.taxable_value_paise / 100:.2f}"
        total_rs = f"{it.line_total_paise / 100:.2f}"
        qty_str = f"{float(it.quantity):.0f} {it.unit}"

        if is_intra:
            cgst_rs = f"{it.cgst_paise / 100:.2f}"
            sgst_rs = f"{it.sgst_paise / 100:.2f}"
            row = [
                Paragraph(str(idx), table_cell_style),
                Paragraph(it.product_name, table_cell_style),
                Paragraph(it.hsn_code, table_cell_style),
                Paragraph(qty_str, table_cell_style),
                Paragraph(rate_rs, table_cell_style),
                Paragraph(taxable_rs, table_cell_style),
                Paragraph(cgst_rs, table_cell_style),
                Paragraph(sgst_rs, table_cell_style),
                Paragraph(total_rs, table_cell_style),
            ]
        else:
            igst_rs = f"{it.igst_paise / 100:.2f}"
            row = [
                Paragraph(str(idx), table_cell_style),
                Paragraph(it.product_name, table_cell_style),
                Paragraph(it.hsn_code, table_cell_style),
                Paragraph(qty_str, table_cell_style),
                Paragraph(rate_rs, table_cell_style),
                Paragraph(taxable_rs, table_cell_style),
                Paragraph(igst_rs, table_cell_style),
                Paragraph(total_rs, table_cell_style),
            ]
        table_rows.append(row)

    # Subtotals & Totals Row
    items_table = Table(table_rows, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8))

    # 4. Summary & Tax Breakup Box
    taxable_sum = f"₹ {invoice.taxable_amount_paise / 100:,.2f}"
    cgst_sum = f"₹ {invoice.cgst_paise / 100:,.2f}"
    sgst_sum = f"₹ {invoice.sgst_paise / 100:,.2f}"
    igst_sum = f"₹ {invoice.igst_paise / 100:,.2f}"
    total_tax_sum = f"₹ {invoice.total_tax_paise / 100:,.2f}"
    grand_total_sum = f"₹ {invoice.grand_total_paise / 100:,.2f}"

    amount_words = number_to_indian_words(int(invoice.grand_total_paise // 100))

    summary_rows = [
        [Paragraph(f"<b>Amount in Words:</b><br/>{amount_words}", body_style), Paragraph("<b>Taxable Value:</b>", body_style), Paragraph(taxable_sum, ParagraphStyle("R", parent=body_style, alignment=2))],
    ]
    if is_intra:
        summary_rows.append([Paragraph("", body_style), Paragraph("<b>CGST (2.5%):</b>", body_style), Paragraph(cgst_sum, ParagraphStyle("R", parent=body_style, alignment=2))])
        summary_rows.append([Paragraph("", body_style), Paragraph("<b>SGST (2.5%):</b>", body_style), Paragraph(sgst_sum, ParagraphStyle("R", parent=body_style, alignment=2))])
    else:
        summary_rows.append([Paragraph("", body_style), Paragraph("<b>IGST (5.0%):</b>", body_style), Paragraph(igst_sum, ParagraphStyle("R", parent=body_style, alignment=2))])

    summary_rows.append([Paragraph("", body_style), Paragraph("<b>Total GST:</b>", body_style), Paragraph(total_tax_sum, ParagraphStyle("R", parent=body_style, alignment=2))])
    summary_rows.append([Paragraph("", body_style), Paragraph("<font size=10 color='#1e3a8a'><b>Grand Total:</b></font>", body_style), Paragraph(f"<font size=10 color='#1e3a8a'><b>{grand_total_sum}</b></font>", ParagraphStyle("R", parent=body_style, alignment=2))])

    summary_table = Table(summary_rows, colWidths=[290, 110, 120])
    summary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (1, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (1, -1), (-1, -1), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # 5. Terms and Signatures
    terms_text = "1. Payment terms: Due on receipt.<br/>2. Goods once sold will not be taken back.<br/>3. Subject to Tiruchirappalli jurisdiction."
    sign_data = [
        [
            Paragraph(f"<b>Terms & Conditions:</b><br/>{terms_text}", body_style),
            Paragraph(f"For <b>{seller_name}</b><br/><br/><br/><br/><b>Authorised Signatory</b>", ParagraphStyle("Sign", parent=body_style, alignment=2)),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[310, 210])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sign_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_delivery_challan_pdf_buffer(dispatch: Any) -> BytesIO:
    """Generate a clean, professional Delivery Challan / Dispatch Note PDF using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    header_sub_style = ParagraphStyle(
        "HeaderSubD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    section_head_style = ParagraphStyle(
        "SectionHeadD",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
    )
    body_style = ParagraphStyle(
        "BodyDarkD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    table_cell_style = ParagraphStyle(
        "TableCellD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBoldD",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
    )

    story = []

    # 1. Header
    seller_name = getattr(settings, "SELLER_COMPANY_NAME", "KANAKKUFLOW FOODS PRIVATE LIMITED")
    seller_gstin = getattr(settings, "SELLER_GSTIN", "33AAAAF1234A1Z5")
    seller_addr = getattr(settings, "SELLER_ADDRESS", "Plot 12, Food Processing SEZ, Thuvakudi, Tiruchirappalli, Tamil Nadu 620015")

    header_data = [
        [
            Paragraph(f"<b>{seller_name}</b><br/>{seller_addr}<br/><b>GSTIN:</b> {seller_gstin}", header_sub_style),
            Paragraph("<font size=14 color='#1e3a8a'><b>DELIVERY CHALLAN</b></font><br/><font size=8 color='#64748b'>DISPATCH & PACKING NOTE</font>", ParagraphStyle("RightHD", parent=header_sub_style, alignment=2)),
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 180])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=8))

    # 2. Meta: Consignee & Transport
    cust = dispatch.customer
    customer_name = cust.customer_name if cust else "Valued Customer"
    cust_addr = f"{cust.shipping_address or cust.billing_address}, {cust.city}, {cust.state} - {cust.pincode}" if cust else ""
    inv_num = getattr(dispatch.invoice, 'invoice_number', 'Pending Invoicing')

    meta_data = [
        [
            Paragraph("<b>DELIVER TO (CONSIGNEE):</b>", section_head_style),
            Paragraph("<b>DISPATCH & TRANSPORT DETAILS:</b>", section_head_style),
        ],
        [
            Paragraph(f"<b>{customer_name}</b><br/>{cust_addr}<br/><b>GSTIN / UIN:</b> {cust.gstin if cust else 'URP'}", body_style),
            Paragraph(
                f"<b>Challan No:</b> {dispatch.dispatch_number}<br/>"
                f"<b>Dispatch Date:</b> {dispatch.dispatch_date.strftime('%d-%b-%Y')}<br/>"
                f"<b>Order Ref:</b> {getattr(dispatch.sales_order, 'order_number', 'N/A')}<br/>"
                f"<b>Invoice Ref:</b> {inv_num}<br/>"
                f"<b>Transporter:</b> {dispatch.transporter_name or 'Factory Vehicle'}<br/>"
                f"<b>Vehicle No:</b> {dispatch.vehicle_number or 'N/A'}<br/>"
                f"<b>Status:</b> {dispatch.status.value}",
                body_style,
            ),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[310, 210])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Item Table
    headers = ["#", "Product Description", "SKU / Code", "Batch Ref", "Quantity Dispatched", "Unit"]
    table_rows = [[Paragraph(f"<b>{h}</b>", table_cell_bold) for h in headers]]

    total_qty = Decimal("0")
    for idx, it in enumerate(dispatch.items, start=1):
        prd = it.product
        qty_num = Decimal(str(it.quantity_dispatched))
        total_qty += qty_num
        row = [
            Paragraph(str(idx), table_cell_style),
            Paragraph(prd.product_name if prd else "Product", table_cell_style),
            Paragraph(prd.sku if prd else "N/A", table_cell_style),
            Paragraph(it.batch_reference or "-", table_cell_style),
            Paragraph(f"{float(qty_num):.0f}", ParagraphStyle("QR", parent=table_cell_style, alignment=2)),
            Paragraph(it.unit, table_cell_style),
        ]
        table_rows.append(row)

    items_table = Table(table_rows, colWidths=[25, 200, 80, 75, 90, 50])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # Total packages box
    tot_data = [
        [
            Paragraph(f"<b>Total Packets Dispatched:</b> {float(total_qty):.0f} Packets", ParagraphStyle("TQ", parent=body_style, fontSize=9)),
        ]
    ]
    tot_table = Table(tot_data, colWidths=[520])
    tot_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tot_table)
    story.append(Spacer(1, 20))

    # 4. Signatures
    sign_data = [
        [
            Paragraph("<b>Received Above Goods in Good Condition:</b><br/><br/><br/><br/>Receiver's Signature & Stamp", body_style),
            Paragraph(f"For <b>{seller_name}</b><br/><br/><br/><br/><b>Authorized Dispatch In-Charge</b>", ParagraphStyle("SD", parent=body_style, alignment=2)),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sign_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_payment_receipt_pdf_buffer(payment: Any) -> BytesIO:
    """Generate an official Payment Receipt PDF using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "ReceiptSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )
    body_style = ParagraphStyle(
        "ReceiptBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )
    table_cell_style = ParagraphStyle(
        "ReceiptTableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    seller_name = getattr(settings, "COMPANY_NAME", "KANAKKUFLOW FOOD PRODUCTS")
    seller_gstin = getattr(settings, "COMPANY_GSTIN", "33AABCF1234F1Z5")
    seller_address = getattr(settings, "COMPANY_ADDRESS", "Plot 12, Food Processing Zone, Thuvakudi, Tiruchirappalli - 620015, Tamil Nadu")

    # Header
    story.append(Paragraph(f"<b>{seller_name}</b>", title_style))
    story.append(Paragraph(f"{seller_address} &bull; GSTIN: <b>{seller_gstin}</b>", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f172a"), spaceBefore=2, spaceAfter=8))
    story.append(Paragraph("<b>OFFICIAL PAYMENT RECEIPT</b>", ParagraphStyle("Hdr", parent=title_style, fontSize=13, textColor=colors.HexColor("#0284c7"))))
    story.append(Spacer(1, 10))

    # Meta Table: Receipt Details & Customer Details
    cust = payment.customer
    meta_data = [
        [
            Paragraph(f"<b>Receipt No:</b> {payment.payment_number}<br/>"
                      f"<b>Date:</b> {payment.payment_date}<br/>"
                      f"<b>Payment Mode:</b> {payment.payment_mode}<br/>"
                      f"<b>Reference / UTR:</b> {payment.reference_number or 'N/A'}<br/>"
                      f"<b>Bank:</b> {payment.bank_name or 'Direct'}", body_style),
            Paragraph(f"<b>Received From:</b><br/>"
                      f"<b>{cust.customer_name if cust else 'Customer'}</b> ({cust.customer_code if cust else 'N/A'})<br/>"
                      f"{cust.billing_address if cust else ''}<br/>"
                      f"{cust.city if cust else ''}, {cust.state if cust else ''} - {cust.pincode if cust else ''}<br/>"
                      f"GSTIN: <b>{cust.gstin if cust and cust.gstin else 'Unregistered'}</b><br/>"
                      f"Phone: {cust.phone if cust else 'N/A'}", body_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # Amount Received Box
    amount_rs = payment.amount_paise / 100
    amount_words = number_to_indian_words(int(amount_rs))
    amt_box = [
        [
            Paragraph(f"<b>AMOUNT RECEIVED:</b> <font size=12 color='#0f766e'><b>₹{amount_rs:,.2f}</b></font><br/>"
                      f"<b>Amount in Words:</b> {amount_words}", body_style)
        ]
    ]
    amt_table = Table(amt_box, colWidths=[520])
    amt_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#16a34a")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(amt_table)
    story.append(Spacer(1, 12))

    # Invoice Allocations Table
    story.append(Paragraph("<b>Invoice Settlement &amp; Allocation Details</b>", ParagraphStyle("SubH", parent=body_style, fontName="Helvetica-Bold", fontSize=10)))
    story.append(Spacer(1, 4))

    alloc_rows = [
        [
            Paragraph("<b>#</b>", table_cell_style),
            Paragraph("<b>Invoice Number</b>", table_cell_style),
            Paragraph("<b>Invoice Date</b>", table_cell_style),
            Paragraph("<b>Invoice Grand Total</b>", ParagraphStyle("HR", parent=table_cell_style, alignment=2)),
            Paragraph("<b>Allocated Amount</b>", ParagraphStyle("HR", parent=table_cell_style, alignment=2)),
        ]
    ]

    tot_alloc_paise = 0
    if payment.allocations:
        for idx, alloc in enumerate(payment.allocations, start=1):
            inv = alloc.invoice
            tot_alloc_paise += alloc.allocated_amount_paise
            inv_total_rs = (inv.grand_total_paise / 100) if inv else 0
            alloc_rs = alloc.allocated_amount_paise / 100
            alloc_rows.append([
                Paragraph(str(idx), table_cell_style),
                Paragraph(inv.invoice_number if inv else "Direct", table_cell_style),
                Paragraph(str(inv.invoice_date) if inv else "-", table_cell_style),
                Paragraph(f"₹{inv_total_rs:,.2f}", ParagraphStyle("CR", parent=table_cell_style, alignment=2)),
                Paragraph(f"₹{alloc_rs:,.2f}", ParagraphStyle("CR", parent=table_cell_style, alignment=2, fontName="Helvetica-Bold")),
            ])
    else:
        alloc_rows.append([
            Paragraph("1", table_cell_style),
            Paragraph("On Account / Advance Payment", table_cell_style),
            Paragraph(str(payment.payment_date), table_cell_style),
            Paragraph("-", ParagraphStyle("CR", parent=table_cell_style, alignment=2)),
            Paragraph(f"₹{amount_rs:,.2f}", ParagraphStyle("CR", parent=table_cell_style, alignment=2, fontName="Helvetica-Bold")),
        ])

    alloc_table = Table(alloc_rows, colWidths=[25, 145, 100, 125, 125])
    alloc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(alloc_table)
    story.append(Spacer(1, 20))

    # Signatures
    sign_data = [
        [
            Paragraph("<b>Terms & Conditions:</b><br/>"
                      "1. Subject to realization of Cheque / Electronic clearance.<br/>"
                      "2. This is a computer generated receipt.", body_style),
            Paragraph(f"For <b>{seller_name}</b><br/><br/><br/><br/><b>Authorized Accounts Signatory</b>", ParagraphStyle("SD", parent=body_style, alignment=2)),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[280, 240])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sign_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
