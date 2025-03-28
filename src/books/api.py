from fastapi import APIRouter, HTTPException, status
from ..books.book_data import books
from ..books.serializers import Book
from typing import List

book_router = APIRouter()


@book_router.get("/all", response_model=List[Book])
async def get_all_books():
    return books


@book_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_a_book(book_data: Book) -> Book:
    new_book = book_data.model_dump()

    books.append(new_book)

    return new_book


@book_router.get("/{book_id}")
async def get_a_book(book_id: int):
    if books[book_id - 1]:
        return books[book_id - 1]
    raise HTTPException(
        status_code=404, detail="Book not found", details="Book not found"
    )
