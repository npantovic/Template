from fastapi import APIRouter, status, Depends
from typing import List
from fastapi.exceptions import HTTPException
from .serializers import UserCreateSerializer
from .model import User
from .service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db.main import get_session
from .dependencies import AccessTokenBearer

auth_router = APIRouter()
user_service = UserService()
access_token_bearer = AccessTokenBearer()


@auth_router.post("/all_users", response_model=List[User])
async def get_all_users(session: AsyncSession = Depends(get_session),): # user_details = Depends(access_token_bearer)
    # role = user_details.get('user', {}).get("role")
    role = "admin"
    if role == "admin":
        users = await user_service.get_all_users(session)
        return users
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not allowed")


@auth_router.post("/singup", response_model=UserCreateSerializer, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateSerializer, session: AsyncSession = Depends(get_session)):
    email = user_data.email
    username = user_data.username
    ucin = user_data.UCIN

    user_exists = await user_service.user_exists(email, username, ucin, session)

    if user_exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists, email, username or UCIN is already taken")

    new_user = await user_service.create_user(user_data, session)

    return new_user