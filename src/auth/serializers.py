from enum import Enum
from typing import List
from datetime import datetime

from pydantic import BaseModel, field_validator, Field
import uuid
import re

class UserSerializer(BaseModel):
    uid: uuid.UUID
    id: int
    username: str
    password_hash: str = Field(exclude=True)
    email: str
    first_name: str
    last_name: str
    UCIN: int
    date_of_birth: str
    gender: str
    is_verified: bool = False
    role: str
    created_at: datetime
    update_at: datetime

class GenderEnumSerializer(str, Enum):
    male = "Male"
    female = "Female"

class UserCreateSerializer(BaseModel):
    username: str = Field(min_length=3, max_length=15)
    email: str = Field(max_length=50)
    password_hash: str = Field(min_length=8)
    first_name: str
    last_name: str
    UCIN: str
    date_of_birth: str
    gender: GenderEnumSerializer

    @field_validator("UCIN")
    @classmethod
    def validate_UCIN(cls, value):
        if not value.isdigit():
            raise ValueError("UCIN must contain only digits")
        if len(value) != 13:
            raise ValueError("UCIN must contain 13 digits")
        return value
    
    @field_validator("password_hash")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return value

class UserCreateAdminModel(BaseModel):
    username: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    UCIN: int
    date_of_birth: str
    gender: GenderEnumSerializer


class UserLoginSerializer(BaseModel):
    email: str
    password_hash: str


class UserChangePasswordSerializer(BaseModel):
    email: str
    password_hash: str



class EmailSerializer(BaseModel):
    addresses: List[str]


class PasswordResetSerializer(BaseModel):
    email: str

class PasswordChangeSerializer(BaseModel):
    new_password: str
    confirm_new_password: str