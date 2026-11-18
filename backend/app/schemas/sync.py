from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from backend.app.schemas.sales import SalesOrderItemCreate


class SyncCustomerItem(BaseModel):
    id: UUID
    customer_code: str
    customer_name: str
    phone: Optional[str] = None
    gstin: Optional[str] = None
    state_code: Optional[str] = None
    credit_limit_paise: int
    is_active: bool


class SyncProductItem(BaseModel):
    id: UUID
    sku: str
    product_name: str
    category: Optional[str] = None
    base_unit: str
    selling_price_paise: int
    gst_rate: Decimal
    hsn_code: Optional[str] = None
    is_active: bool


class SyncReferenceDataResponse(BaseModel):
    timestamp: datetime
    customers: List[SyncCustomerItem]
    products: List[SyncProductItem]


class ClientSyncOrder(BaseModel):
    client_order_uuid: str
    customer_id: UUID
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[SalesOrderItemCreate] = Field(..., min_length=1)


class SyncOrdersRequest(BaseModel):
    orders: List[ClientSyncOrder]


class SyncedOrderItem(BaseModel):
    client_order_uuid: str
    sales_order_id: UUID
    order_number: str
    grand_total_paise: int
    status: str


class FailedOrderItem(BaseModel):
    client_order_uuid: str
    error: str


class SyncOrdersResponse(BaseModel):
    synced: List[SyncedOrderItem]
    failed: List[FailedOrderItem]
