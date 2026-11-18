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
from backend.app.models.inventory import InventoryItemType


class ProductionRunStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class OverheadExpenseType(str, enum.Enum):
    LABOUR = "LABOUR"
    GAS = "GAS"
    POWER = "POWER"
    OTHER = "OTHER"


class VarianceStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ProductionRun(Base, TimestampMixin):
    __tablename__ = "production_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    run_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    bom_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("boms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    bom_version_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    production_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    number_of_batches: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("1.00"),
        nullable=False,
    )
    expected_output: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    actual_good_output: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    damaged_packaging: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    wastage_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    status: Mapped[ProductionRunStatus] = mapped_column(
        Enum(ProductionRunStatus, name="production_run_status_enum", native_enum=False),
        default=ProductionRunStatus.DRAFT,
        nullable=False,
        index=True,
    )
    planned_material_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    actual_material_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    packaging_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    labour_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    utility_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_production_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cost_per_packet_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cost_per_packet_decimal: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    variance_status: Mapped[VarianceStatus] = mapped_column(
        Enum(VarianceStatus, name="variance_status_enum", native_enum=False),
        default=VarianceStatus.NORMAL,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supervisor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    posted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    product = relationship("Product")
    bom = relationship("BOM")
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    materials: Mapped[List["ProductionRunMaterial"]] = relationship(
        "ProductionRunMaterial",
        back_populates="production_run",
        cascade="all, delete-orphan",
    )
    overheads: Mapped[List["ProductionRunOverhead"]] = relationship(
        "ProductionRunOverhead",
        back_populates="production_run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ProductionRun {self.run_number} ({self.status}) - Output: {self.actual_good_output}>"


class ProductionRunMaterial(Base):
    __tablename__ = "production_run_materials"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    production_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("production_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[InventoryItemType] = mapped_column(
        Enum(InventoryItemType, name="prod_mat_item_type_enum", native_enum=False),
        nullable=False,
    )
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    issued_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    consumed_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    planned_unit_cost: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    actual_unit_cost: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    material_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    consumption_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    production_run: Mapped["ProductionRun"] = relationship(
        "ProductionRun",
        back_populates="materials",
    )

    def __repr__(self) -> str:
        return f"<ProductionRunMaterial {self.item_type} {self.item_id}: {self.consumed_quantity} {self.unit}>"


class ProductionRunOverhead(Base):
    __tablename__ = "production_run_overheads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    production_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("production_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expense_type: Mapped[OverheadExpenseType] = mapped_column(
        Enum(OverheadExpenseType, name="overhead_expense_type_enum", native_enum=False),
        nullable=False,
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    production_run: Mapped["ProductionRun"] = relationship(
        "ProductionRun",
        back_populates="overheads",
    )

    def __repr__(self) -> str:
        return f"<ProductionRunOverhead {self.expense_type}: ₹{self.amount_paise/100:.2f}>"
