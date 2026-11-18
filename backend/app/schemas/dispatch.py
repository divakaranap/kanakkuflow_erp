from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.dispatch import DispatchStatus


class DispatchItemCreate(BaseModel):
    sales_order_item_id: str
    product_id: str
    quantity_dispatched: Decimal = Field(..., gt=0)
    batch_reference: Optional[str] = None


class DispatchItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dispatch_id: str
    sales_order_item_id: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    quantity_dispatched: Decimal
    batch_reference: Optional[str] = None
    unit: str
    created_at: datetime


class DispatchCreate(BaseModel):
    sales_order_id: str
    invoice_id: Optional[str] = None
    dispatch_date: Optional[date] = None
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    tracking_reference: Optional[str] = None
    notes: Optional[str] = None
    items: List[DispatchItemCreate] = Field(..., min_length=1)


class DispatchUpdate(BaseModel):
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    tracking_reference: Optional[str] = None
    notes: Optional[str] = None


class DispatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dispatch_number: str
    sales_order_id: str
    order_number: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = None
    dispatch_date: date
    status: DispatchStatus
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    tracking_reference: Optional[str] = None
    notes: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    dispatched_by: Optional[int] = None
    dispatched_at: Optional[datetime] = None
    created_at: datetime
    items: List[DispatchItemResponse] = []


class OrderItemDispatchStatus(BaseModel):
    sales_order_item_id: str
    product_id: str
    product_name: str
    ordered_quantity: Decimal
    fulfilled_quantity: Decimal
    pending_quantity: Decimal
    available_stock_quantity: Decimal
    has_sufficient_stock: bool


class OrderDispatchStatusResponse(BaseModel):
    sales_order_id: str
    order_number: str
    customer_id: str
    customer_name: str
    order_status: str
    items: List[OrderItemDispatchStatus]
    can_dispatch: bool
