from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.sales import SalesOrderStatus, InvoiceStatus


# --- Items ---
class SalesOrderItemBase(BaseModel):
    product_id: UUID
    ordered_quantity: Decimal = Field(..., gt=0, description="Quantity ordered")
    unit_price_paise: Optional[int] = Field(None, ge=0, description="Optional override; defaults to customer price list")
    discount_paise: int = Field(0, ge=0)


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sales_order_id: UUID
    product_id: UUID
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    ordered_quantity: Decimal
    fulfilled_quantity: Decimal
    unit_price_paise: int
    discount_paise: int
    gst_rate: Decimal
    taxable_amount_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    line_total_paise: int


# --- Sales Order ---
class SalesOrderCreate(BaseModel):
    customer_id: UUID
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[SalesOrderItemCreate] = Field(..., min_length=1)


class SalesOrderUpdate(BaseModel):
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    items: Optional[List[SalesOrderItemCreate]] = None


class SalesOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    customer_id: UUID
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    order_date: date
    delivery_date: Optional[date] = None
    place_of_supply_state_code: str
    customer_gstin: Optional[str] = None
    status: SalesOrderStatus
    subtotal_paise: int
    discount_paise: int
    taxable_amount_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_tax_paise: int
    grand_total_paise: int
    notes: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[SalesOrderItemResponse] = []


# --- Invoice Items ---
class SalesInvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    product_id: Optional[UUID] = None
    product_name: str
    hsn_code: str
    quantity: Decimal
    unit: str
    unit_price_paise: int
    taxable_value_paise: int
    gst_rate: Decimal
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    line_total_paise: int


# --- Invoices ---
class SalesInvoiceCreate(BaseModel):
    sales_order_id: UUID
    invoice_date: Optional[date] = None


class InvoiceCancelRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=3, description="Audit reason for cancelling invoice")


class SalesInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    sales_order_id: UUID
    order_number: Optional[str] = None
    customer_id: UUID
    customer_name: Optional[str] = None
    customer_gstin: Optional[str] = None
    invoice_date: date
    place_of_supply_state_code: str
    seller_gstin: str
    buyer_gstin: Optional[str] = None
    taxable_amount_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_tax_paise: int
    grand_total_paise: int
    status: InvoiceStatus
    pdf_path: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    items: List[SalesInvoiceItemResponse] = []


# --- Stock Check ---
class ProductStockCheckResponse(BaseModel):
    product_id: UUID
    sku: str
    product_name: str
    requested_qty: Decimal
    available_qty: Decimal
    is_sufficient: bool
    shortage_qty: Decimal
