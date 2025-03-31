from fastapi import FastAPI

from contextlib import asynccontextmanager
from src.db.main import init_db

# ================================routes imports===============================

from src.books.api import book_router
from src.auth.api import auth_router

# =============================================================================


@asynccontextmanager
async def life_span(app: FastAPI):
    print("server is starting...")
    await init_db()
    yield
    print("server has been stopped...")


version = "v1"

app = FastAPI(
    title="Template FastAPI",
    description="Template FastAPI project",
    version=version,
    lifespan=life_span,
)


# ================================routes include===============================

app.include_router(book_router, prefix=f"/api/{version}/books", tags=["Books"])

app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=["Users"])

# =============================================================================
