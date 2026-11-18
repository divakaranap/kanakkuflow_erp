import enum
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException

from backend.app.models.payment import (
    CustomerPayment,
    PaymentAllocation,
    CustomerLedgerEntry,
    PaymentMode,
    PaymentStatus,
)
from backend.app.models.sales import SalesInvoice, InvoiceStatus
from backend.app.models.customer import Customer
from backend.app.schemas.payment import (
    CustomerPaymentCreate,
    CustomerLedgerStatementResponse,
    CustomerLedgerEntryResponse,
    ReceivablesAgeingSummaryResponse,
    ReceivablesAgeingCustomer,
)


def generate_payment_number(db: Session) -> str:
    """Generate sequential Receipt Number: RCP-YYYYMM-XXXX."""
    today = date.today()
    prefix = f"RCP-{today.strftime('%Y%m')}-"
    last_payment = (
        db.query(CustomerPayment)
        .filter(CustomerPayment.payment_number.like(f"{prefix}%"))
        .order_by(desc(CustomerPayment.payment_number))
        .first()
    )
    if last_payment:
        try:
            last_seq = int(last_payment.payment_number.split("-")[-1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1
    return f"{prefix}{new_seq:04d}"


def ensure_invoice_in_ledger(db: Session, invoice: SalesInvoice) -> None:
    """Ensure a posted sales invoice exists in the customer ledger."""
    existing = (
        db.query(CustomerLedgerEntry)
        .filter(
            CustomerLedgerEntry.customer_id == str(invoice.customer_id),
            CustomerLedgerEntry.reference_document_id == str(invoice.id),
            CustomerLedgerEntry.entry_type == "INVOICE",
        )
        .first()
    )
    if existing:
        return

    # Find previous running balance
    current_bal = (
        db.query(func.coalesce(func.sum(CustomerLedgerEntry.debit_paise - CustomerLedgerEntry.credit_paise), 0))
        .filter(CustomerLedgerEntry.customer_id == str(invoice.customer_id))
        .scalar()
    )
    new_balance = current_bal + invoice.grand_total_paise

    ledger_entry = CustomerLedgerEntry(
        customer_id=str(invoice.customer_id),
        entry_date=invoice.invoice_date,
        entry_type="INVOICE",
        reference_document_id=str(invoice.id),
        reference_number=invoice.invoice_number,
        debit_paise=invoice.grand_total_paise,
        credit_paise=0,
        running_balance_paise=new_balance,
        description=f"Sales Invoice #{invoice.invoice_number}",
    )
    db.add(ledger_entry)
    db.flush()


def record_customer_payment(
    db: Session,
    data: CustomerPaymentCreate,
    current_user_id: int,
) -> CustomerPayment:
    """Record customer payment with atomic invoice allocation and ledger posting."""
    cust_id_str = str(data.customer_id)
    customer = db.query(Customer).filter(Customer.id == cust_id_str).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {data.customer_id} not found")

    if data.amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    allocations_in = data.allocations or []
    total_allocated = sum(a.allocated_amount_paise for a in allocations_in)
    if total_allocated > data.amount_paise:
        raise HTTPException(
            status_code=400,
            detail=f"Total allocated amount (₹{total_allocated/100:.2f}) cannot exceed payment amount (₹{data.amount_paise/100:.2f})",
        )

    # Validate allocations against unpaid invoices
    validated_invoices = []
    for alloc_item in allocations_in:
        inv_id_str = str(alloc_item.invoice_id)
        invoice = db.query(SalesInvoice).filter(SalesInvoice.id == inv_id_str).first()
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {alloc_item.invoice_id} not found")

        if str(invoice.customer_id) != cust_id_str:
            raise HTTPException(
                status_code=400,
                detail=f"Invoice {invoice.invoice_number} does not belong to customer {customer.customer_name}",
            )

        if invoice.status != InvoiceStatus.POSTED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot allocate payment to non-posted invoice {invoice.invoice_number} (status: {invoice.status})",
            )

        # Make sure this invoice is reflected in customer ledger
        ensure_invoice_in_ledger(db, invoice)

        remaining_unpaid = invoice.grand_total_paise - (invoice.amount_paid_paise or 0)
        if alloc_item.allocated_amount_paise > remaining_unpaid:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Allocation of ₹{alloc_item.allocated_amount_paise/100:.2f} exceeds remaining unpaid balance "
                    f"of ₹{remaining_unpaid/100:.2f} for Invoice {invoice.invoice_number}"
                ),
            )
        validated_invoices.append((invoice, alloc_item.allocated_amount_paise))

    # Generate payment record
    pay_num = generate_payment_number(db)
    pay_date = data.payment_date or date.today()

    payment = CustomerPayment(
        payment_number=pay_num,
        customer_id=cust_id_str,
        payment_date=pay_date,
        amount_paise=data.amount_paise,
        payment_mode=data.payment_mode,
        reference_number=data.reference_number,
        bank_name=data.bank_name,
        status=PaymentStatus.CLEARED if data.payment_mode in [PaymentMode.CASH, PaymentMode.UPI, PaymentMode.NEFT, PaymentMode.RTGS] else PaymentStatus.RECORDED,
        notes=data.notes,
        created_by=current_user_id,
    )
    db.add(payment)
    db.flush()

    # Create allocations and update invoice amount_paid_paise
    for invoice, alloc_paise in validated_invoices:
        alloc_record = PaymentAllocation(
            payment_id=str(payment.id),
            invoice_id=str(invoice.id),
            allocated_amount_paise=alloc_paise,
        )
        db.add(alloc_record)
        invoice.amount_paid_paise = (invoice.amount_paid_paise or 0) + alloc_paise

    # Update Customer Ledger
    current_bal = (
        db.query(func.coalesce(func.sum(CustomerLedgerEntry.debit_paise - CustomerLedgerEntry.credit_paise), 0))
        .filter(CustomerLedgerEntry.customer_id == cust_id_str)
        .scalar()
    )
    new_balance = current_bal - data.amount_paise

    ledger_entry = CustomerLedgerEntry(
        customer_id=cust_id_str,
        entry_date=pay_date,
        entry_type="PAYMENT",
        reference_document_id=str(payment.id),
        reference_number=payment.payment_number,
        debit_paise=0,
        credit_paise=data.amount_paise,
        running_balance_paise=new_balance,
        description=f"Payment received via {payment.payment_mode} (Ref: {payment.reference_number or 'Direct'})",
    )
    db.add(ledger_entry)

    db.commit()
    db.refresh(payment)
    return payment


def get_customer_ledger_statement(
    db: Session,
    customer_id: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> CustomerLedgerStatementResponse:
    """Generate running statement of account for customer."""
    cust_id_str = str(customer_id)
    customer = db.query(Customer).filter(Customer.id == cust_id_str).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    query = db.query(CustomerLedgerEntry).filter(CustomerLedgerEntry.customer_id == cust_id_str)
    if from_date:
        query = query.filter(CustomerLedgerEntry.entry_date >= from_date)
    if to_date:
        query = query.filter(CustomerLedgerEntry.entry_date <= to_date)

    entries = query.order_by(CustomerLedgerEntry.entry_date.asc(), CustomerLedgerEntry.created_at.asc(), CustomerLedgerEntry.id.asc()).all()

    total_debit = sum(e.debit_paise for e in entries)
    total_credit = sum(e.credit_paise for e in entries)
    closing_balance = total_debit - total_credit

    running = 0
    formatted_entries = []
    for e in entries:
        running += (e.debit_paise - e.credit_paise)
        formatted_entries.append(
            CustomerLedgerEntryResponse(
                id=e.id,
                customer_id=e.customer_id,
                entry_date=e.entry_date,
                entry_type=e.entry_type,
                reference_document_id=e.reference_document_id,
                reference_number=e.reference_number,
                debit_paise=e.debit_paise,
                credit_paise=e.credit_paise,
                running_balance_paise=running,
                description=e.description,
                created_at=e.created_at,
            )
        )

    return CustomerLedgerStatementResponse(
        customer_id=cust_id_str,
        customer_name=customer.customer_name,
        customer_code=customer.customer_code,
        phone=customer.phone,
        gstin=customer.gstin,
        opening_balance_paise=0,
        total_debit_paise=total_debit,
        total_credit_paise=total_credit,
        closing_balance_paise=closing_balance,
        entries=formatted_entries,
    )


def get_receivables_ageing_report(
    db: Session,
    as_of_date: Optional[date] = None,
) -> ReceivablesAgeingSummaryResponse:
    """Generate Accounts Receivable Ageing Report bucketed by 0-30, 31-60, 61-90, >90 days."""
    target_date = as_of_date or date.today()

    # Get all posted invoices that have remaining unpaid balance
    invoices = (
        db.query(SalesInvoice)
        .filter(
            SalesInvoice.status == InvoiceStatus.POSTED,
            SalesInvoice.grand_total_paise > func.coalesce(SalesInvoice.amount_paid_paise, 0),
        )
        .all()
    )

    customer_map: Dict[str, Dict[str, Any]] = {}

    for inv in invoices:
        cust_id = str(inv.customer_id)
        if cust_id not in customer_map:
            cust = inv.customer
            customer_map[cust_id] = {
                "customer_id": cust_id,
                "customer_name": cust.customer_name if cust else "Customer",
                "customer_code": cust.customer_code if cust else "N/A",
                "total_outstanding_paise": 0,
                "not_due_paise": 0,
                "days_0_to_30_paise": 0,
                "days_31_to_60_paise": 0,
                "days_61_to_90_paise": 0,
                "days_over_90_paise": 0,
            }

        unpaid = inv.grand_total_paise - (inv.amount_paid_paise or 0)
        customer_map[cust_id]["total_outstanding_paise"] += unpaid

        # Age calculation based on invoice_date
        days = (target_date - inv.invoice_date).days

        if days <= 0:
            customer_map[cust_id]["not_due_paise"] += unpaid
        elif days <= 30:
            customer_map[cust_id]["days_0_to_30_paise"] += unpaid
        elif days <= 60:
            customer_map[cust_id]["days_31_to_60_paise"] += unpaid
        elif days <= 90:
            customer_map[cust_id]["days_61_to_90_paise"] += unpaid
        else:
            customer_map[cust_id]["days_over_90_paise"] += unpaid

    customer_list = [ReceivablesAgeingCustomer(**c) for c in customer_map.values()]

    return ReceivablesAgeingSummaryResponse(
        as_of_date=target_date,
        total_receivables_paise=sum(c.total_outstanding_paise for c in customer_list),
        total_not_due_paise=sum(c.not_due_paise for c in customer_list),
        total_0_to_30_paise=sum(c.days_0_to_30_paise for c in customer_list),
        total_31_to_60_paise=sum(c.days_31_to_60_paise for c in customer_list),
        total_61_to_90_paise=sum(c.days_61_to_90_paise for c in customer_list),
        total_over_90_paise=sum(c.days_over_90_paise for c in customer_list),
        customers=customer_list,
    )
