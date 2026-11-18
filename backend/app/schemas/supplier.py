import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from backend.app.utils.validators import validate_gstin, validate_phone, get_state_code


class SupplierBase(BaseModel):
    supplier_code: str
    supplier_name: str
    contact_person: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    gstin: str
    address: str
    city: str
    state: str
    state_code: Optional[str] = None
    pincode: str
    payment_terms: Optional[str] = "Net 30"
    is_active: bool = True

    @field_validator("gstin")
    @classmethod
    def check_gstin(cls, v: str) -> str:
        clean = v.strip().upper()
        if not validate_gstin(clean):
            raise ValueError(f"Invalid Indian GSTIN format: '{v}'")
        return clean

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        if not validate_phone(v):
            raise ValueError(f"Invalid Indian phone number: '{v}'")
        return v.strip()

    @model_validator(mode="after")
    def compute_state_code(self) -> "SupplierBase":
        if not self.state_code:
            if self.gstin and len(self.gstin) >= 2 and self.gstin[:2].isdigit():
                self.state_code = self.gstin[:2]
            elif self.state:
                code = get_state_code(self.state)
                self.state_code = code if code else "33"
            else:
                self.state_code = "33"
        return self


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    pincode: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("gstin")
    @classmethod
    def check_gstin_opt(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean = v.strip().upper()
            if not validate_gstin(clean):
                raise ValueError("Invalid Indian GSTIN format")
            return clean
        return v

    @field_validator("phone")
    @classmethod
    def check_phone_opt(cls, v: Optional[str]) -> Optional[str]:
        if v:
            if not validate_phone(v):
                raise ValueError("Invalid Indian phone number")
            return v.strip()
        return v


class SupplierOut(SupplierBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
