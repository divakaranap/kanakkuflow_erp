import datetime
import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, Enum, BigInteger, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class PriceListCustomerType(str, enum.Enum):
    RETAILER = "RETAILER"
    DISTRIBUTOR = "DISTRIBUTOR"
    ALL = "ALL"


class PriceList(Base, TimestampMixin):
    __tablename__ = "price_lists"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_type: Mapped[PriceListCustomerType] = mapped_column(
        Enum(PriceListCustomerType, name="price_list_customer_type_enum", native_enum=False),
        nullable=False,
        default=PriceListCustomerType.ALL,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    items: Mapped[List["PriceListItem"]] = relationship(
        "PriceListItem",
        back_populates="price_list",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PriceList {self.name} ({self.customer_type})>"


class PriceListItem(Base, TimestampMixin):
    __tablename__ = "price_list_items"
    __table_args__ = (
        UniqueConstraint("price_list_id", "product_id", name="uq_price_list_product"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    price_list_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("price_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selling_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    valid_from: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    price_list: Mapped["PriceList"] = relationship("PriceList", back_populates="items")
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<PriceListItem {self.price_list_id} - {self.product_id} - {self.selling_price_paise}p>"
