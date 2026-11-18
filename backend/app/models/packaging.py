import enum
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Enum, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class PackagingCategory(str, enum.Enum):
    POUCH = "POUCH"
    CARTON = "CARTON"
    LABEL = "LABEL"
    TAPE = "TAPE"
    OTHER = "OTHER"


class PackagingItem(Base, TimestampMixin):
    __tablename__ = "packaging_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    packaging_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    packaging_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    category: Mapped[PackagingCategory] = mapped_column(
        Enum(PackagingCategory, name="packaging_category_enum", native_enum=False),
        nullable=False,
        default=PackagingCategory.POUCH,
    )
    base_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="piece")
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<PackagingItem {self.packaging_code} - {self.packaging_name}>"
