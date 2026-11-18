import enum
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String,
    Enum,
    Numeric,
    BigInteger,
    Text,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class InventoryItemType(str, enum.Enum):
    RAW = "RAW"
    PACKAGING = "PACKAGING"
    FG = "FG"  # Finished Goods


class MovementType(str, enum.Enum):
    OPENING = "OPENING"
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    PRODUCTION_ISSUE = "PRODUCTION_ISSUE"
    PRODUCTION_OUTPUT = "PRODUCTION_OUTPUT"
    PRODUCTION_SCRAP = "PRODUCTION_SCRAP"
    INVOICE_DISPATCH = "INVOICE_DISPATCH"
    CREDIT_NOTE = "CREDIT_NOTE"
    ADJUSTMENT = "ADJUSTMENT"


class AdjustmentType(str, enum.Enum):
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"


class AdjustmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    item_type: Mapped[InventoryItemType] = mapped_column(
        Enum(InventoryItemType, name="inventory_item_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, name="stock_movement_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    qty_delta: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )
    unit_cost_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_value_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<StockMovement {self.movement_type} {self.item_type} {self.item_id}: {self.qty_delta}>"


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("item_type", "item_id", "batch_id", name="uq_inventory_balance_item_batch"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    item_type: Mapped[InventoryItemType] = mapped_column(
        Enum(InventoryItemType, name="inventory_balance_item_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    cached_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    total_value_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    weighted_avg_rate_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_reconciled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class InventoryAdjustment(Base, TimestampMixin):
    __tablename__ = "inventory_adjustments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    adjustment_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    item_type: Mapped[InventoryItemType] = mapped_column(
        Enum(InventoryItemType, name="adj_item_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    adjustment_type: Mapped[AdjustmentType] = mapped_column(
        Enum(AdjustmentType, name="adj_type_enum", native_enum=False),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[AdjustmentStatus] = mapped_column(
        Enum(AdjustmentStatus, name="adj_status_enum", native_enum=False),
        nullable=False,
        default=AdjustmentStatus.DRAFT,
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    posted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
