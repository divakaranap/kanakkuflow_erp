import enum
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Enum, BigInteger, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class ProductCategory(str, enum.Enum):
    MURUKKU = "MURUKKU"
    MIXTURE = "MIXTURE"
    CHIPS = "CHIPS"
    SWEETS = "SWEETS"
    OTHER = "OTHER"


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory, name="product_category_enum", native_enum=False),
        nullable=False,
        default=ProductCategory.MURUKKU,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pack_size: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("200.00"))
    pack_size_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="g")
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=False, default="1905")
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0500"))
    selling_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=5000)
    base_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="packet")
    packets_per_carton: Mapped[int] = mapped_column(nullable=False, default=20)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Product {self.sku} - {self.product_name}>"
