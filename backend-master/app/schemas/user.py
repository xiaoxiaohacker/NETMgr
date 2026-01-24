from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str

    class Config:
        from_attributes = True  # ✅ 兼容 Pydantic V2

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"