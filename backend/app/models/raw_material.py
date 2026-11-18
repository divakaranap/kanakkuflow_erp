import enum
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Enum, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class RawMaterialCategory(str, enum.Enum):
    FLOUR = "FLOUR"
    OIL = "OIL"
    SPICE = "SPICE"
    OTHER = "OTHER"


class RawMaterial(Base, TimestampMixin):
    __tablename__ = "raw_materials"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    material_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    material_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    category: Mapped[RawMaterialCategory] = mapped_column(
        Enum(RawMaterialCategory, name="raw_material_category_enum", native_enum=False),
        nullable=False,
        default=RawMaterialCategory.OTHER,
    )
    base_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<RawMaterial {self.material_code} - {self.material_name}>"
