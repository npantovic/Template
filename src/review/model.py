# from __future__ import annotations

# from sqlmodel import SQLModel, Field, Column, Relationship
# import sqlalchemy.dialects.postgresql as pg
# from sqlalchemy import Integer, ForeignKey
# from datetime import datetime
# import uuid

# from typing import Optional, List, TYPE_CHECKING

# if TYPE_CHECKING:
#     from src.apartment.model import Apartment
#     from src.auth.model import User


# class Review(SQLModel, table=True):
#     __tablename__ = "reviews"

#     uid: uuid.UUID = Field(
#         sa_column=Column(
#             pg.UUID(as_uuid=True), nullable=False,
#             primary_key=True, default=uuid.uuid4
#         )
#     )
#     id: Optional[int] = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))

#     apartment_id: Optional[uuid.UUID] = Field(default=None, foreign_key="apartments.uid")
#     user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")

#     rating: float
#     comment: Optional[str] = None
#     created_at: datetime = Field(default_factory=datetime.now)

#     apartment: "Apartment" = Relationship(back_populates="reviews")
#     user: "User" = Relationship(back_populates="reviews")