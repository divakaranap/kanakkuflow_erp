from decimal import Decimal
from typing import Optional, Dict, List
from pydantic import BaseModel


class UnitConvertRequest(BaseModel):
    quantity: str
    from_unit: str
    to_unit: str
    packets_per_carton: Optional[int] = None


class UnitConvertResponse(BaseModel):
    original_quantity: str
    converted_quantity: str
    from_unit: str
    to_unit: str
    packets_per_carton: Optional[int] = None


class SupportedUnitsResponse(BaseModel):
    categories: Dict[str, List[str]]
    base_units: List[str]
