import enum
from datetime import date, datetime
from typing import Optional, List
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin


class DispatchStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    DISPATCHED = "DISPATCHED"
    CANCELLED = "CANCELLED"


class Dispatch(Base, TimestampMixin):
    __tablename__ = "dispatches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    dispatch_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    sales_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sales_invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    dispatch_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    status: Mapped[DispatchStatus] = mapped_column(
        Enum(DispatchStatus, name="dispatch_status_enum", native_enum=False),
        default=DispatchStatus.DRAFT,
        nullable=False,
        index=True,
    )
    transporter_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tracking_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    dispatched_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder")
    invoice: Mapped[Optional["SalesInvoice"]] = relationship("SalesInvoice")
    customer: Mapped["Customer"] = relationship("Customer")
    items: Mapped[List["DispatchItem"]] = relationship(
        "DispatchItem", back_populates="dispatch", cascade="all, delete-orphan", order_by="DispatchItem.id"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    dispatcher: Mapped[Optional["User"]] = relationship("User", foreign_keys=[dispatched_by])


class DispatchItem(Base):
    __tablename__ = "dispatch_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    dispatch_id: Mapped[str] = mapped_column(String(36), ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_order_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_dispatched: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    batch_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="packet", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    # Relationships
    dispatch: Mapped["Dispatch"] = relationship("Dispatch", back_populates="items")
    sales_order_item: Mapped["SalesOrderItem"] = relationship("SalesOrderItem")
    product: Mapped["Product"] = relationship("Product")
