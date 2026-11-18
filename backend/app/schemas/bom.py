from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.bom import BOMStatus
from backend.app.models.inventory import InventoryItemType


class BOMItemCreate(BaseModel):
    item_type: InventoryItemType
    item_id: str
    quantity_per_batch: Decimal = Field(..., gt=0, description="Standard quantity required for one batch")
    unit: str = Field(..., description="Unit of measurement e.g. kg, litre, piece")


class BOMItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bom_id: str
    item_type: InventoryItemType
    item_id: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    quantity_per_batch: Decimal
    unit: str
    created_at: datetime


class BOMCreate(BaseModel):
    product_id: str
    batch_yield_packets: Decimal = Field(default=Decimal("200.0000"), gt=0)
    tolerance_pct: Decimal = Field(default=Decimal("3.00"), ge=0, le=100)
    description: Optional[str] = None
    items: List[BOMItemCreate] = Field(..., min_length=1)


class BOMUpdate(BaseModel):
    batch_yield_packets: Optional[Decimal] = None
    tolerance_pct: Optional[Decimal] = None
    description: Optional[str] = None
    items: Optional[List[BOMItemCreate]] = None


class BOMOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bom_code: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    version: int
    batch_yield_packets: Decimal
    tolerance_pct: Decimal
    description: Optional[str] = None
    status: BOMStatus
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: List[BOMItemOut] = []


class BOMPlannedItem(BaseModel):
    item_type: InventoryItemType
    item_id: str
    item_code: str
    item_name: str
    quantity_per_batch: Decimal
    planned_quantity: Decimal
    unit: str
    available_stock: Decimal
    is_sufficient: bool


class BOMScalingResponse(BaseModel):
    bom_id: str
    bom_code: str
    version: int
    product_id: str
    product_name: str
    product_sku: str
    number_of_batches: Decimal
    batch_yield_packets: Decimal
    expected_output_packets: Decimal
    tolerance_pct: Decimal
    items: List[BOMPlannedItem]
