import enum
import uuid
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    Enum,
    Numeric,
    Text,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin
from backend.app.models.inventory import InventoryItemType


class BOMStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class BOM(Base, TimestampMixin):
    __tablename__ = "boms"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    bom_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    batch_yield_packets: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        default=Decimal("200.0000"),
        nullable=False,
    )
    tolerance_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("3.00"),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[BOMStatus] = mapped_column(
        Enum(BOMStatus, name="bom_status_enum", native_enum=False),
        default=BOMStatus.DRAFT,
        nullable=False,
        index=True,
    )
    effective_from: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    effective_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    product = relationship("Product")
    creator = relationship("User", foreign_keys=[created_by])
    items: Mapped[List["BOMItem"]] = relationship(
        "BOMItem",
        back_populates="bom",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BOM {self.bom_code} v{self.version} ({self.status})>"


class BOMItem(Base):
    __tablename__ = "bom_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    bom_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("boms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[InventoryItemType] = mapped_column(
        Enum(InventoryItemType, name="bom_item_type_enum", native_enum=False),
        nullable=False,
    )
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    quantity_per_batch: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    bom: Mapped["BOM"] = relationship("BOM", back_populates="items")

    def __repr__(self) -> str:
        return f"<BOMItem {self.bom_id} {self.item_type} {self.item_id}: {self.quantity_per_batch} {self.unit}>"
