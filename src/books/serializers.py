from pydantic import BaseModel
from datetime import datetime
import uuid


class Book(BaseModel):
    uid: uuid.UUID
    id: int
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str
    created_at: datetime
    update_at: datetime


class BookCreateModel(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str


class BookResponse(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    description: str


class BookUpdateModel(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    edition_number: int
    number_of_copies: int
    description: str
