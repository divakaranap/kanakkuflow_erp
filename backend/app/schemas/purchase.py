from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.purchase import PurchaseStatus, PurchaseItemType


class PurchaseLineCreate(BaseModel):
    item_type: PurchaseItemType
    item_id: str
    quantity: Decimal = Field(..., gt=0, description="Quantity in purchase units")
    unit: str = Field(..., description="Unit of measurement used in invoice, e.g. kg, g, litre")
    unit_rate_paise: int = Field(..., ge=0, description="Rate per unit in paise")
    tax_rate: Decimal = Field(default=Decimal("0.0500"), ge=0, le=1, description="GST rate, e.g. 0.05 for 5%")
    batch_number: Optional[str] = None
    manufacturing_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class PurchaseLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    purchase_id: str
    item_type: PurchaseItemType
    item_id: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    quantity: Decimal
    unit: str
    normalized_quantity: Decimal
    unit_rate_paise: int
    taxable_value_paise: int
    tax_rate: Decimal
    tax_paise: int
    line_total_paise: int
    batch_number: Optional[str] = None
    manufacturing_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class PurchaseCreate(BaseModel):
    supplier_id: str
    supplier_invoice_number: str = Field(..., min_length=1)
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[PurchaseLineCreate] = Field(..., min_length=1)


class PurchaseUpdate(BaseModel):
    supplier_invoice_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: Optional[List[PurchaseLineCreate]] = None


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    purchase_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    supplier_invoice_number: str
    purchase_date: datetime
    status: PurchaseStatus
    subtotal_paise: int
    tax_paise: int
    total_paise: int
    notes: Optional[str] = None
    created_by: int
    posted_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseLineOut] = []
