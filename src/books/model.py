from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Integer
from datetime import datetime
import uuid


class Book(SQLModel, table=True):
    __tablename__ = "books"
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, nullable=False,
            primary_key=True, default=uuid.uuid4
        )
    )
    id: int = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now()))
    update_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now()))

    def __repr__(self):
        return f"<Book {self.title}>"
