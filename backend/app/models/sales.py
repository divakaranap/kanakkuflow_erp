import enum
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, BigInteger, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin


class SalesOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    place_of_supply_state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    customer_gstin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[SalesOrderStatus] = mapped_column(
        Enum(SalesOrderStatus, name="sales_order_status_enum", native_enum=False),
        default=SalesOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )
    subtotal_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    discount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    taxable_amount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    igst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_tax_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    grand_total_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer")
    items: Mapped[List["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="order", cascade="all, delete-orphan", order_by="SalesOrderItem.id"
    )
    invoices: Mapped[List["SalesInvoice"]] = relationship("SalesInvoice", back_populates="sales_order")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    sales_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    fulfilled_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    taxable_amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    igst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    line_total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="items")
    product: Mapped["Product"] = relationship("Product")


class SalesInvoice(Base, TimestampMixin):
    __tablename__ = "sales_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    sales_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    place_of_supply_state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    seller_gstin: Mapped[str] = mapped_column(String(20), nullable=False)
    buyer_gstin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    taxable_amount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    igst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_tax_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    grand_total_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="sales_invoice_status_enum", native_enum=False),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amount_paid_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="invoices")
    customer: Mapped["Customer"] = relationship("Customer")
    items: Mapped[List["SalesInvoiceItem"]] = relationship(
        "SalesInvoiceItem", back_populates="invoice", cascade="all, delete-orphan", order_by="SalesInvoiceItem.id"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class SalesInvoiceItem(Base):
    __tablename__ = "sales_invoice_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="packet", nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    taxable_value_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    cgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sgst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    igst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    line_total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    invoice: Mapped["SalesInvoice"] = relationship("SalesInvoice", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")
