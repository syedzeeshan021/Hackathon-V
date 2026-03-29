from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr

class UserBackground(str, Enum):
    SOFTWARE = "SOFTWARE"
    HARDWARE = "HARDWARE"
    BOTH = "BOTH"
    NONE = "NONE"

class UserBase(BaseModel):
    email: EmailStr
    background: UserBackground = UserBackground.NONE

class UserCreate(UserBase):
    # password_hash will be managed by Better-Auth.com, not directly created here
    pass

class UserInDB(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    password_hash: str # Stored hash

    class Config:
        from_attributes = True # Pydantic v2: orm_mode=True is deprecated