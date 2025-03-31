from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Integer
from datetime import datetime
import uuid
from typing import Optional


class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    id: int = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    username: str
    password_hash: str = Field(exclude=True)
    email: str
    first_name: str
    last_name: str
    UCIN: str
    date_of_birth: str
    gender: str
    is_verified: bool = False
    role: str = Field(default="clan")
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now()))
    update_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now()))

    def __repr__(self):
        return f"<User {self.username}>"
