from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.production import (
    ProductionRunStatus,
    OverheadExpenseType,
    VarianceStatus,
)
from backend.app.models.inventory import InventoryItemType


class ProductionRunMaterialCreate(BaseModel):
    item_type: InventoryItemType
    item_id: str
    issued_quantity: Decimal = Field(..., ge=0)
    consumed_quantity: Optional[Decimal] = None
    unit: str


class ProductionRunOverheadCreate(BaseModel):
    expense_type: OverheadExpenseType
    amount_paise: int = Field(..., ge=0)
    description: Optional[str] = None


class ProductionRunCreate(BaseModel):
    product_id: str
    bom_id: Optional[str] = None
    batch_number: str = Field(..., min_length=1)
    number_of_batches: Decimal = Field(default=Decimal("1.00"), gt=0)
    actual_good_output: Decimal = Field(default=Decimal("0.0000"), ge=0)
    damaged_packaging: Decimal = Field(default=Decimal("0.0000"), ge=0)
    wastage_quantity: Decimal = Field(default=Decimal("0.0000"), ge=0)
    production_date: Optional[datetime] = None
    notes: Optional[str] = None
    materials: Optional[List[ProductionRunMaterialCreate]] = None
    overheads: Optional[List[ProductionRunOverheadCreate]] = None


class ProductionRunUpdate(BaseModel):
    batch_number: Optional[str] = None
    number_of_batches: Optional[Decimal] = None
    actual_good_output: Optional[Decimal] = None
    damaged_packaging: Optional[Decimal] = None
    wastage_quantity: Optional[Decimal] = None
    production_date: Optional[datetime] = None
    notes: Optional[str] = None
    materials: Optional[List[ProductionRunMaterialCreate]] = None
    overheads: Optional[List[ProductionRunOverheadCreate]] = None


class ProductionRunMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    production_run_id: str
    item_type: InventoryItemType
    item_id: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    planned_quantity: Decimal
    issued_quantity: Decimal
    consumed_quantity: Decimal
    unit: str
    planned_unit_cost: int
    actual_unit_cost: int
    material_cost_paise: int
    consumption_variance_pct: Decimal


class ProductionRunOverheadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    production_run_id: str
    expense_type: OverheadExpenseType
    amount_paise: int
    description: Optional[str] = None
    created_at: datetime


class ProductionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_number: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    bom_id: str
    bom_code: Optional[str] = None
    production_date: datetime
    batch_number: str
    number_of_batches: Decimal
    expected_output: Decimal
    actual_good_output: Decimal
    damaged_packaging: Decimal
    wastage_quantity: Decimal
    status: ProductionRunStatus
    planned_material_cost_paise: int
    actual_material_cost_paise: int
    packaging_cost_paise: int
    labour_cost_paise: int
    utility_cost_paise: int
    total_production_cost_paise: int
    cost_per_packet_paise: int
    cost_per_packet_decimal: Decimal
    variance_status: VarianceStatus
    notes: Optional[str] = None
    supervisor_id: int
    created_at: datetime
    posted_at: Optional[datetime] = None
    materials: List[ProductionRunMaterialOut] = []
    overheads: List[ProductionRunOverheadOut] = []


class VarianceItem(BaseModel):
    item_type: str
    item_id: str
    item_code: str
    item_name: str
    planned_quantity: Decimal
    actual_quantity: Decimal
    unit: str
    difference: Decimal
    variance_pct: Decimal
    tolerance_pct: Decimal
    status: str  # "OK", "WARNING", "CRITICAL"


class ProductionVarianceReport(BaseModel):
    production_run_id: str
    run_number: str
    expected_output: Decimal
    actual_good_output: Decimal
    yield_difference: Decimal
    yield_variance_pct: Decimal
    yield_status: str
    material_variances: List[VarianceItem]
    has_alerts: bool
    alerts: List[str]


class ProductionCostingReport(BaseModel):
    production_run_id: str
    run_number: str
    actual_good_output: Decimal
    raw_materials_cost_paise: int
    packaging_cost_paise: int
    total_material_cost_paise: int
    labour_cost_paise: int
    utility_cost_paise: int
    total_overheads_paise: int
    total_production_cost_paise: int
    cost_per_packet_paise: int
    cost_per_packet_decimal: Decimal
    selling_price_paise: int
    gross_margin_paise: int
    gross_margin_pct: Decimal
    material_breakdown: List[Dict[str, Any]]
