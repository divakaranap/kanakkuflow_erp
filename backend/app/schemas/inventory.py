from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.inventory import (
    InventoryItemType,
    MovementType,
    AdjustmentType,
    AdjustmentStatus,
)


class OpeningStockCreate(BaseModel):
    item_type: InventoryItemType
    item_id: str
    quantity: Decimal = Field(..., gt=0, description="Quantity in base units")
    unit_cost_paise: int = Field(..., ge=0, description="Unit cost in paise")
    notes: Optional[str] = "Opening stock"
    batch_id: Optional[str] = None
    reference_number: Optional[str] = "OPENING"


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: InventoryItemType
    item_id: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    batch_id: Optional[str] = None
    movement_type: MovementType
    qty_delta: Decimal
    unit_cost_paise: Optional[int] = None
    total_value_paise: Optional[int] = None
    source_type: str
    source_id: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime


class StockSummaryItem(BaseModel):
    item_type: InventoryItemType
    item_id: str
    item_code: str
    item_name: str
    category: Optional[str] = None
    base_unit: str
    current_stock: Decimal
    reorder_level: Decimal
    is_low_stock: bool
    weighted_avg_rate_paise: int
    total_valuation_paise: int
    last_updated: Optional[datetime] = None


class StockValuationItem(BaseModel):
    item_type: InventoryItemType
    item_id: str
    item_code: str
    item_name: str
    base_unit: str
    quantity: Decimal
    weighted_avg_rate_paise: int
    total_value_paise: int


class StockValuationSummary(BaseModel):
    total_valuation_paise: int
    total_items: int
    raw_materials_valuation_paise: int
    packaging_valuation_paise: int
    finished_goods_valuation_paise: int
    items: List[StockValuationItem]


class StockReconciliationItem(BaseModel):
    item_type: InventoryItemType
    item_id: str
    item_code: str
    item_name: str
    base_unit: str
    ledger_qty: Decimal
    cached_qty: Decimal
    difference: Decimal
    status: str  # "MATCHED", "MISMATCH"


class StockReconciliationReport(BaseModel):
    reconciled_at: datetime
    total_items: int
    matched_items: int
    mismatched_items: int
    is_fully_reconciled: bool
    items: List[StockReconciliationItem]


class AdjustmentCreate(BaseModel):
    item_type: InventoryItemType
    item_id: str
    adjustment_type: AdjustmentType
    quantity: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=3)
    reference_number: Optional[str] = None


class AdjustmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    adjustment_number: str
    item_type: InventoryItemType
    item_id: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    adjustment_type: AdjustmentType
    quantity: Decimal
    reason: str
    reference_number: Optional[str] = None
    status: AdjustmentStatus
    created_by: int
    approved_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
