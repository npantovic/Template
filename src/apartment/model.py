# Apartment model
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from src.auth.model import User

class Apartment(SQLModel, table=True):
    __tablename__ = "apartments"

    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True
    )

    title: str
    description: str
    country: str
    city: str
    state: str
    address: str
    zip_code: str
    latitude: float
    longitude: float

    price: float
    currency: str = Field(default="EUR")
    discount_percentage: float = Field(default=0.0)
    cleaning_fee: float = Field(default=0.0)
    deposit_amount: float = Field(default=0.0)

    num_rooms: int
    num_beds: int
    square_meters: float

    floor: int
    has_elevator: bool = Field(default=False)
    has_wifi: bool = Field(default=False)
    has_air_conditioning: bool = Field(default=False)
    has_parking: bool = Field(default=False)
    pet_friendly: bool = Field(default=False)

    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    owner_id: uuid.UUID = Field(foreign_key="users.uid")
    # Use SQLModel's Relationship instead of SQLAlchemy's relationship
    # owner: Optional["User"] = Relationship(back_populates="apartments")

    def __repr__(self):
        return f"<Apartment {self.title}>"


# class ApartmentImage(SQLModel, table=True):
#     __tablename__ = "apartment_images"

#     id: int = Field(default=None, primary_key=True)
#     apartment_id: Optional[uuid.UUID] = Field(
#         default=None,
#         sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("apartments.uid"))
#     )
#     image_url: str

#     apartment: Mapped[Optional["Apartment"]] = Relationship(back_populates="images")

#     def __repr__(self):
#         return f"<ApartmentImage for apartment_id={self.apartment_id}>"