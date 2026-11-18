from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.payment import PaymentMode, PaymentStatus


class AllocationCreate(BaseModel):
    invoice_id: str
    allocated_amount_paise: int = Field(gt=0, description="Amount in paise to allocate to invoice")


class AllocationResponse(BaseModel):
    id: str
    payment_id: str
    invoice_id: str
    invoice_number: Optional[str] = None
    allocated_amount_paise: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerPaymentCreate(BaseModel):
    customer_id: str
    payment_date: Optional[date] = None
    amount_paise: int = Field(gt=0, description="Total payment amount in paise")
    payment_mode: PaymentMode = PaymentMode.NEFT
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    allocations: Optional[List[AllocationCreate]] = Field(default_factory=list)


class CustomerPaymentResponse(BaseModel):
    id: str
    payment_number: str
    customer_id: str
    customer_name: Optional[str] = None
    payment_date: date
    amount_paise: int
    payment_mode: PaymentMode
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    status: PaymentStatus
    notes: Optional[str] = None
    created_by: int
    created_at: datetime
    allocations: List[AllocationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CustomerLedgerEntryResponse(BaseModel):
    id: str
    customer_id: str
    entry_date: date
    entry_type: str
    reference_document_id: Optional[str] = None
    reference_number: str
    debit_paise: int
    credit_paise: int
    running_balance_paise: int
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerLedgerStatementResponse(BaseModel):
    customer_id: str
    customer_name: str
    customer_code: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    opening_balance_paise: int = 0
    total_debit_paise: int = 0
    total_credit_paise: int = 0
    closing_balance_paise: int = 0
    entries: List[CustomerLedgerEntryResponse] = Field(default_factory=list)


class ReceivablesAgeingCustomer(BaseModel):
    customer_id: str
    customer_name: str
    customer_code: Optional[str] = None
    total_outstanding_paise: int
    not_due_paise: int
    days_0_to_30_paise: int
    days_31_to_60_paise: int
    days_61_to_90_paise: int
    days_over_90_paise: int


class ReceivablesAgeingSummaryResponse(BaseModel):
    as_of_date: date
    total_receivables_paise: int
    total_not_due_paise: int
    total_0_to_30_paise: int
    total_31_to_60_paise: int
    total_61_to_90_paise: int
    total_over_90_paise: int
    customers: List[ReceivablesAgeingCustomer] = Field(default_factory=list)
