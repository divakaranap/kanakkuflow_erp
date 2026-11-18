import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from backend.app.models.raw_material import RawMaterialCategory
from backend.app.services.unit_conversion_service import normalize_unit_name, validate_unit


class RawMaterialBase(BaseModel):
    material_code: str
    material_name: str
    category: RawMaterialCategory = RawMaterialCategory.OTHER
    base_unit: str = "kg"
    reorder_level: Decimal = Decimal("0.0000")
    description: Optional[str] = None
    is_active: bool = True

    @field_validator("base_unit")
    @classmethod
    def check_base_unit(cls, v: str) -> str:
        norm = normalize_unit_name(v)
        if not validate_unit("RAW_MATERIAL", norm):
            raise ValueError(f"Invalid raw material unit '{v}'. Supported: kg, g, litre, ml")
        return norm

    @field_validator("reorder_level")
    @classmethod
    def check_reorder_level(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Reorder level cannot be negative")
        return v


class RawMaterialCreate(RawMaterialBase):
    pass


class RawMaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    category: Optional[RawMaterialCategory] = None
    base_unit: Optional[str] = None
    reorder_level: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("base_unit")
    @classmethod
    def check_base_unit_opt(cls, v: Optional[str]) -> Optional[str]:
        if v:
            norm = normalize_unit_name(v)
            if not validate_unit("RAW_MATERIAL", norm):
                raise ValueError(f"Invalid raw material unit '{v}'")
            return norm
        return v


class RawMaterialOut(RawMaterialBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
