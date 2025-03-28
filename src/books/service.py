from sqlmodel.ext.asyncio.session import AsyncSession
from .serializers import BookCreateModel, BookUpdateModel


class BookService:
    async def get_all_book(self, session: AsyncSession):
        pass

    async def get_book(self, book_uid: str, session: AsyncSession):
        pass

    async def create_book(self, book_data: BookCreateModel, session: AsyncSession):
        pass

    async def update_book(self, book_data: BookUpdateModel, session: AsyncSession):
        pass

    async def delete_book(self, book_uid: str, session: AsyncSession):
        pass
