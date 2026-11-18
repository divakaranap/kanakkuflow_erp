import enum
import uuid
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Enum,
    Numeric,
    BigInteger,
    Text,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class PurchaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class PurchaseItemType(str, enum.Enum):
    RAW = "RAW"
    PACKAGING = "PACKAGING"


class Purchase(Base, TimestampMixin):
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    purchase_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    purchase_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus, name="purchase_status_enum", native_enum=False),
        nullable=False,
        default=PurchaseStatus.DRAFT,
        index=True,
    )
    subtotal_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    tax_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    posted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    posted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    supplier = relationship("Supplier")
    creator = relationship("User", foreign_keys=[created_by])
    poster = relationship("User", foreign_keys=[posted_by])
    lines: Mapped[List["PurchaseLine"]] = relationship(
        "PurchaseLine",
        back_populates="purchase",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Purchase {self.purchase_number} - {self.status} - ₹{self.total_paise/100:.2f}>"


class PurchaseLine(Base):
    __tablename__ = "purchase_lines"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    purchase_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[PurchaseItemType] = mapped_column(
        Enum(PurchaseItemType, name="purchase_item_type_enum", native_enum=False),
        nullable=False,
    )
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    normalized_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_rate_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    taxable_value_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0500"), nullable=False)
    tax_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    line_total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    manufacturing_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="lines")

    def __repr__(self) -> str:
        return f"<PurchaseLine {self.purchase_id} item {self.item_id}: {self.quantity} {self.unit}>"
