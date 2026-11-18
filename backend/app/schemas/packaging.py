import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from backend.app.models.packaging import PackagingCategory
from backend.app.services.unit_conversion_service import normalize_unit_name, validate_unit


class PackagingBase(BaseModel):
    packaging_code: str
    packaging_name: str
    category: PackagingCategory = PackagingCategory.POUCH
    base_unit: str = "piece"
    reorder_level: Decimal = Decimal("0.0000")
    description: Optional[str] = None
    is_active: bool = True

    @field_validator("base_unit")
    @classmethod
    def check_base_unit(cls, v: str) -> str:
        norm = normalize_unit_name(v)
        if not validate_unit("PACKAGING", norm):
            raise ValueError(f"Invalid packaging unit '{v}'. Supported: piece")
        return norm

    @field_validator("reorder_level")
    @classmethod
    def check_reorder_level(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Reorder level cannot be negative")
        return v


class PackagingCreate(PackagingBase):
    pass


class PackagingUpdate(BaseModel):
    packaging_name: Optional[str] = None
    category: Optional[PackagingCategory] = None
    base_unit: Optional[str] = None
    reorder_level: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PackagingOut(PackagingBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
