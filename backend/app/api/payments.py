from typing import List, Optional
from datetime import date
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.models.payment import CustomerPayment, PaymentAllocation
from backend.app.models.sales import SalesInvoice, InvoiceStatus
from backend.app.schemas.payment import (
    CustomerPaymentCreate,
    CustomerPaymentResponse,
    CustomerLedgerStatementResponse,
    ReceivablesAgeingSummaryResponse,
    AllocationResponse,
)
from backend.app.schemas.sales import SalesInvoiceResponse
from backend.app.services.payment_service import (
    record_customer_payment,
    get_customer_ledger_statement,
    get_receivables_ageing_report,
)
from backend.app.services.pdf_service import generate_payment_receipt_pdf_buffer

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "",
    response_model=CustomerPaymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN]))],
)
def create_payment(
    data: CustomerPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a customer payment with optional atomic invoice allocations."""
    payment = record_customer_payment(db, data, current_user.id)
    return CustomerPaymentResponse(
        id=payment.id,
        payment_number=payment.payment_number,
        customer_id=payment.customer_id,
        customer_name=payment.customer.customer_name if payment.customer else None,
        payment_date=payment.payment_date,
        amount_paise=payment.amount_paise,
        payment_mode=payment.payment_mode,
        reference_number=payment.reference_number,
        bank_name=payment.bank_name,
        status=payment.status,
        notes=payment.notes,
        created_by=payment.created_by,
        created_at=payment.created_at,
        allocations=[
            AllocationResponse(
                id=a.id,
                payment_id=a.payment_id,
                invoice_id=a.invoice_id,
                invoice_number=a.invoice.invoice_number if a.invoice else None,
                allocated_amount_paise=a.allocated_amount_paise,
                created_at=a.created_at,
            )
            for a in payment.allocations
        ],
    )


@router.get(
    "",
    response_model=List[CustomerPaymentResponse],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN, UserRole.AUDITOR]))],
)
def list_payments(
    customer_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List recorded customer payments."""
    query = (
        db.query(CustomerPayment)
        .options(
            joinedload(CustomerPayment.customer),
            joinedload(CustomerPayment.allocations).joinedload(PaymentAllocation.invoice),
        )
        .order_by(desc(CustomerPayment.payment_date), desc(CustomerPayment.created_at))
    )
    if customer_id:
        query = query.filter(CustomerPayment.customer_id == str(customer_id))

    payments = query.all()
    return [
        CustomerPaymentResponse(
            id=p.id,
            payment_number=p.payment_number,
            customer_id=p.customer_id,
            customer_name=p.customer.customer_name if p.customer else None,
            payment_date=p.payment_date,
            amount_paise=p.amount_paise,
            payment_mode=p.payment_mode,
            reference_number=p.reference_number,
            bank_name=p.bank_name,
            status=p.status,
            notes=p.notes,
            created_by=p.created_by,
            created_at=p.created_at,
            allocations=[
                AllocationResponse(
                    id=a.id,
                    payment_id=a.payment_id,
                    invoice_id=a.invoice_id,
                    invoice_number=a.invoice.invoice_number if a.invoice else None,
                    allocated_amount_paise=a.allocated_amount_paise,
                    created_at=a.created_at,
                )
                for a in p.allocations
            ],
        )
        for p in payments
    ]


@router.get(
    "/receivables/ageing",
    response_model=ReceivablesAgeingSummaryResponse,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN, UserRole.AUDITOR]))],
)
def get_receivables_ageing(
    as_of: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Accounts receivable ageing report bucketed by Not Due, 0-30, 31-60, 61-90, and >90 days."""
    return get_receivables_ageing_report(db, as_of)


@router.get(
    "/ledger/{customer_id}",
    response_model=CustomerLedgerStatementResponse,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN, UserRole.AUDITOR]))],
)
def get_customer_ledger(
    customer_id: str,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Fetch chronological statement of account ledger entries with running balance for customer."""
    return get_customer_ledger_statement(db, customer_id, from_date, to_date)


@router.get(
    "/unpaid-invoices/{customer_id}",
    response_model=List[dict],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN]))],
)
def get_unpaid_invoices(
    customer_id: str,
    db: Session = Depends(get_db),
):
    """Get all posted invoices for a customer with remaining unpaid balances."""
    invoices = (
        db.query(SalesInvoice)
        .filter(
            SalesInvoice.customer_id == str(customer_id),
            SalesInvoice.status == InvoiceStatus.POSTED,
            SalesInvoice.grand_total_paise > SalesInvoice.amount_paid_paise,
        )
        .order_by(SalesInvoice.invoice_date.asc())
        .all()
    )
    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "grand_total_paise": inv.grand_total_paise,
            "amount_paid_paise": inv.amount_paid_paise,
            "remaining_unpaid_paise": inv.grand_total_paise - inv.amount_paid_paise,
        }
        for inv in invoices
    ]


@router.get(
    "/{payment_id}",
    response_model=CustomerPaymentResponse,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN, UserRole.AUDITOR]))],
)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """Get single payment details."""
    payment = (
        db.query(CustomerPayment)
        .options(
            joinedload(CustomerPayment.customer),
            joinedload(CustomerPayment.allocations).joinedload(PaymentAllocation.invoice),
        )
        .filter(CustomerPayment.id == str(payment_id))
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return CustomerPaymentResponse(
        id=payment.id,
        payment_number=payment.payment_number,
        customer_id=payment.customer_id,
        customer_name=payment.customer.customer_name if payment.customer else None,
        payment_date=payment.payment_date,
        amount_paise=payment.amount_paise,
        payment_mode=payment.payment_mode,
        reference_number=payment.reference_number,
        bank_name=payment.bank_name,
        status=payment.status,
        notes=payment.notes,
        created_by=payment.created_by,
        created_at=payment.created_at,
        allocations=[
            AllocationResponse(
                id=a.id,
                payment_id=a.payment_id,
                invoice_id=a.invoice_id,
                invoice_number=a.invoice.invoice_number if a.invoice else None,
                allocated_amount_paise=a.allocated_amount_paise,
                created_at=a.created_at,
            )
            for a in payment.allocations
        ],
    )


@router.get(
    "/{payment_id}/receipt",
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SALESMAN, UserRole.AUDITOR]))],
)
def download_payment_receipt_pdf(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """Download official payment receipt PDF."""
    payment = (
        db.query(CustomerPayment)
        .options(
            joinedload(CustomerPayment.customer),
            joinedload(CustomerPayment.allocations).joinedload(PaymentAllocation.invoice),
        )
        .filter(CustomerPayment.id == str(payment_id))
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    buffer: BytesIO = generate_payment_receipt_pdf_buffer(payment)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Receipt_{payment.payment_number}.pdf"'},
    )
