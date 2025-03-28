from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from ..books.serializers import Book, BookCreateModel
from typing import List
from src.books.service import BookService

from src.db.main import get_session
from sqlalchemy.ext.asyncio import AsyncSession

book_router = APIRouter()
book_service = BookService()


@book_router.get("/all", response_model=List[Book])
async def get_all_books(session: AsyncSession = Depends(get_session)):
    books = await book_service.get_all_books(session)

    return books


@book_router.post("/create", status_code=status.HTTP_201_CREATED, response_model=Book)
async def create_a_book(book_data: BookCreateModel, session: AsyncSession = Depends(get_session)) -> dict:
    new_book = await book_service.create_book(book_data, session)

    return new_book


@book_router.get("/{book_id}")
async def get_book(book_uid: str, session: AsyncSession = Depends(get_session)):
    book = await book_service.get_book(book_uid, session)

    if book:
        return book
    else:
        raise HTTPException(
            status_code=404, detail="Book not found", details="Book not found"
        )
