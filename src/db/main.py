from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from src.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

# ======================MODEL TO CREATE IN DB========================
from src.auth.model import User
from src.books.model import Book
# ===================================================================

engine = AsyncEngine(create_engine(url=Config.DATABASE_URL, echo=True))


async def init_db() -> None:
    async with engine.begin() as conn:
        # proverava da sve imporovane modele i kreira ih u bazi
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with Session() as session:
        yield session
