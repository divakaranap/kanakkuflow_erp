import enum
import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Enum, BigInteger, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class CustomerType(str, enum.Enum):
    RETAILER = "RETAILER"
    DISTRIBUTOR = "DISTRIBUTOR"


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    customer_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    customer_type: Mapped[CustomerType] = mapped_column(
        Enum(CustomerType, name="customer_type_enum", native_enum=False),
        nullable=False,
        default=CustomerType.RETAILER,
    )
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gstin: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    
    price_list_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("price_lists.id", ondelete="SET NULL"),
        nullable=True,
    )
    credit_limit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    assigned_salesman_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    assigned_salesman = relationship("User", foreign_keys=[assigned_salesman_id])
    price_list = relationship("PriceList", foreign_keys=[price_list_id])

    def __repr__(self) -> str:
        return f"<Customer {self.customer_code} - {self.customer_name}>"
