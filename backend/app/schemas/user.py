from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from backend.app.models.user import UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
