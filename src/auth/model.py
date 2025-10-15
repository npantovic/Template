from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import uuid
from enum import Enum

if TYPE_CHECKING:
    from src.apartment.model import Apartment

class GenderEnum(str, Enum):
    male = "male"
    female = "female"

class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True
    )

    username: str
    password_hash: str
    email: str
    first_name: str
    last_name: str
    UCIN: str
    date_of_birth: str
    gender: GenderEnum
    is_verified: bool = Field(default=False)
    role: str = Field(default="clan")

    totp_secret: Optional[str] = None
    enabled_2fa: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Use SQLModel's Relationship instead of SQLAlchemy's
    # apartments: List["Apartment"] = Relationship(back_populates="owner")

    def __repr__(self):
        return f"<User {self.username}>"