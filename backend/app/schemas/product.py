import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from backend.app.models.product import ProductCategory


class ProductBase(BaseModel):
    sku: str
    product_name: str
    category: ProductCategory = ProductCategory.MURUKKU
    description: Optional[str] = None
    pack_size: Decimal = Decimal("200.00")
    pack_size_unit: str = "g"
    hsn_code: str = "1905"
    gst_rate: Decimal = Decimal("0.0500")
    selling_price_paise: int = 5000
    base_unit: str = "packet"
    packets_per_carton: int = 20
    reorder_level: Decimal = Decimal("0.0000")
    is_active: bool = True

    @field_validator("selling_price_paise")
    @classmethod
    def check_selling_price(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Selling price must be strictly positive (got {v} paise)")
        return v

    @field_validator("packets_per_carton")
    @classmethod
    def check_packets_per_carton(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Packets per carton must be strictly positive (got {v})")
        return v

    @field_validator("pack_size")
    @classmethod
    def check_pack_size(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Pack size must be positive")
        return v

    @field_validator("reorder_level")
    @classmethod
    def check_reorder_level(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Reorder level cannot be negative")
        return v

    @field_validator("gst_rate")
    @classmethod
    def check_gst_rate(cls, v: Decimal) -> Decimal:
        if v < 0 or v > Decimal("0.50"):
            raise ValueError("GST rate must be between 0% and 50% (e.g., 0.05 for 5%)")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[ProductCategory] = None
    description: Optional[str] = None
    pack_size: Optional[Decimal] = None
    pack_size_unit: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[Decimal] = None
    selling_price_paise: Optional[int] = None
    base_unit: Optional[str] = None
    packets_per_carton: Optional[int] = None
    reorder_level: Optional[Decimal] = None
    is_active: Optional[bool] = None

    @field_validator("selling_price_paise")
    @classmethod
    def check_selling_price_opt(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Selling price must be strictly positive")
        return v

    @field_validator("packets_per_carton")
    @classmethod
    def check_packets_opt(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Packets per carton must be strictly positive")
        return v


class ProductOut(ProductBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
