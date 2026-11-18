import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from backend.app.models.price_list import PriceListCustomerType


class PriceListItemBase(BaseModel):
    product_id: str
    selling_price_paise: int
    valid_from: Optional[datetime.datetime] = None
    valid_until: Optional[datetime.datetime] = None

    @field_validator("selling_price_paise")
    @classmethod
    def check_price(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Price must be strictly positive (got {v} paise)")
        return v


class PriceListItemCreate(PriceListItemBase):
    pass


class PriceListItemOut(PriceListItemBase):
    id: str
    price_list_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    product_sku: Optional[str] = None
    product_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PriceListBase(BaseModel):
    name: str
    description: Optional[str] = None
    customer_type: PriceListCustomerType = PriceListCustomerType.ALL
    is_active: bool = True


class PriceListCreate(PriceListBase):
    items: Optional[List[PriceListItemCreate]] = None


class PriceListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    customer_type: Optional[PriceListCustomerType] = None
    is_active: Optional[bool] = None


class PriceListOut(PriceListBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: List[PriceListItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class EffectivePriceResponse(BaseModel):
    product_id: str
    sku: str
    product_name: str
    selling_price_paise: int
    source: str  # 'CUSTOMER_PRICE_LIST', 'CUSTOMER_TYPE_PRICE_LIST', or 'PRODUCT_DEFAULT'
    price_list_id: Optional[str] = None
    price_list_name: Optional[str] = None
