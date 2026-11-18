import enum
from datetime import date, datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, BigInteger, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin


class PaymentMode(str, enum.Enum):
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    NEFT = "NEFT"
    RTGS = "RTGS"
    UPI = "UPI"


class PaymentStatus(str, enum.Enum):
    RECORDED = "RECORDED"
    CLEARED = "CLEARED"
    BOUNCED = "BOUNCED"


class CustomerPayment(Base, TimestampMixin):
    __tablename__ = "customer_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    payment_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(
        Enum(PaymentMode, name="payment_mode_enum", native_enum=False),
        default=PaymentMode.NEFT,
        nullable=False,
    )
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum", native_enum=False),
        default=PaymentStatus.RECORDED,
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer")
    allocations: Mapped[List["PaymentAllocation"]] = relationship(
        "PaymentAllocation", back_populates="payment", cascade="all, delete-orphan", order_by="PaymentAllocation.id"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class PaymentAllocation(Base, TimestampMixin):
    __tablename__ = "payment_allocations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    payment_id: Mapped[str] = mapped_column(String(36), ForeignKey("customer_payments.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_invoices.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    payment: Mapped["CustomerPayment"] = relationship("CustomerPayment", back_populates="allocations")
    invoice: Mapped["SalesInvoice"] = relationship("SalesInvoice")


class CustomerLedgerEntry(Base, TimestampMixin):
    __tablename__ = "customer_ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)  # INVOICE, PAYMENT, OPENING_BALANCE, REVERSAL
    reference_document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False)
    debit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)   # Increases receivable (Invoice)
    credit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # Decreases receivable (Payment)
    running_balance_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer")
