from .model import User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .serializers import UserCreateSerializer
from .utils import generate_password_hash
from sqlalchemy import or_
from fastapi import Depends, HTTPException, status
import re

import pyotp
import qrcode
from io import BytesIO

MAX_FAILED_ATTEMPTS = 5
BLOCK_DURATION_SECONDS = 600  # 10 minuta
import redis
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

class UserService:

    async def get_all_users(self, session: AsyncSession):
        statement = select(User).order_by(User.uid)

        result = await session.exec(statement)

        return result.all()


    # ==================================================================================================


    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)

        result = await session.exec(statement)

        user = result.first()

        return user


    async def get_user_by_first_name(self, first_name: str, session: AsyncSession):
        statement = select(User).where(User.first_name == first_name)

        result = await session.exec(statement)

        user = result.all()

        return user


    async def get_user_by_username(self, username: str, session: AsyncSession):
        statement = select(User).where(User.username == username)

        result = await session.exec(statement)

        user = result.first()

        return user


    async def get_user_by_last_name(self, last_name: str, session: AsyncSession):
        statement = select(User).where(User.last_name == last_name)

        result = await session.exec(statement)

        user = result.all()

        return user


    async def get_user_by_date_of_birth(self, date_of_birth: str, session: AsyncSession):
        statement = select(User).where(User.date_of_birth == date_of_birth)

        result = await session.exec(statement)

        user = result.all()

        return user


    async def get_user_by_UCIN(self, UCIN: str, session: AsyncSession):
        statement = select(User).where(User.UCIN == UCIN)

        result = await session.exec(statement)

        user = result.first()

        return user


    async def get_user_by_gender(self, gender: str, session: AsyncSession):
        statement = select(User).where(User.gender == gender)

        result = await session.exec(statement)

        user = result.all()

        return user


    async def get_user_by_uid(self, uid: str, session: AsyncSession):
        statement = select(User).where(User.uid == uid)

        result = await session.exec(statement)

        user = result.first()

        return user


    # ==================================================================================================


    async def user_exists(self, email: str, username: str, ucin: str, session: AsyncSession):
        result = await session.exec(
            select(User).where((User.email == email) | (User.username == username) | (User.UCIN == ucin))
        )
        return result.first() is not None


    async def create_user(self, user_data: UserCreateSerializer, session: AsyncSession):
        user_data_dict = user_data.model_dump()

        new_user = User(
            **user_data_dict
        )

        new_user.password_hash = generate_password_hash(user_data_dict["password_hash"])

        session.add(new_user)

        await session.commit()

        return new_user


    async def create_user_admin(self, user_data: UserCreateSerializer, session: AsyncSession):
        user_data_dict = user_data.model_dump()

        new_user = User(
            **user_data_dict
        )

        new_user.password_hash = generate_password_hash(user_data_dict["password_hash"])
        new_user.role = "admin"
        new_user.is_verified = True

        session.add(new_user)

        await session.commit()

        return new_user


    async def create_user_some_role(self, user_data: UserCreateSerializer, session: AsyncSession):
        user_data_dict = user_data.model_dump()

        new_user = User(
            **user_data_dict
        )

        new_user.password_hash = generate_password_hash(user_data_dict["password_hash"])
        new_user.role = "role_name"
        # new_user.is_approved = True
        # new_user.is_active = True

        session.add(new_user)

        await session.commit()

        return new_user

    # ==================================================================================================

    #TODO
    async def update_password(self):
        pass


    async def delete_user(self, user_uid: str, session: AsyncSession):
        user_to_delete = await self.get_user_by_uid(user_uid, session)

        if user_to_delete is not None:
            await session.delete(user_to_delete)

            await session.commit()

            return {}

        else:
            return None


    async def approve_user(self, user: User, user_data: dict, session: AsyncSession):
        for k, v in user_data.items():
            setattr(user, k, v)
        await session.commit()

        return user


    async def update_user_email_verify(self, user: User, user_data: dict, session: AsyncSession):
        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user


    # ==================================================================================================

    async def update_username(self, user_uid: str, new_username: str, session: AsyncSession):
        existing_user = await self.get_user_by_username(new_username, session)
        if existing_user:
            raise ValueError("Username is already taken")

        user = await self.get_user_by_uid(user_uid, session)
        if not user:
            raise ValueError("User not found")

        user.username = new_username
        await session.commit()
        await session.refresh(user)

        return user
    

    async def update_email(self, user_uid: str, new_email: str, session: AsyncSession):
        existing_user = await self.get_user_by_email(new_email, session)
        if existing_user:
            raise ValueError("Email is already taken")

        user = await self.get_user_by_uid(user_uid, session)
        if not user:
            raise ValueError("User not found")

        user.email = new_email
        await session.commit()
        await session.refresh(user)

        return user
    

    async def update_totp(self, user_uid: str, new_totp: str, session: AsyncSession):
        user = await self.get_user_by_uid(user_uid, session)
        if not user:
            raise ValueError("User not found")

        user.totp_secret = new_totp
        await session.commit()
        await session.refresh(user)


    async def update_enabled_2fa(self, user_uid: str, session: AsyncSession):
        user = await self.get_user_by_uid(user_uid, session)
        if not user:
            raise ValueError("User not found")

        user.enabled_2fa = True
        await session.commit()
        await session.refresh(user)


    async def validate_password_complexity(self, password: str):
        """
        Validates the complexity of a password.
        """
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        if not re.search(r"[A-Z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )
        if not re.search(r"[a-z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter"
            )
        if not re.search(r"\d", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number"
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character"
            )
        

    # ==================================================================================================


    def generate_secret(self):
        return pyotp.random_base32()


    def get_qr_code(self, username: str, secret: str):
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="MyApp")
        img = qrcode.make(otp_uri)
        buf = BytesIO()
        img.save(buf)
        buf.seek(0)
        return buf
    
    async def deactivate_2FA(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        if not user:
            raise ValueError("User not found")

        user.totp_secret = ""
        user.enabled_2fa = False
        session.add(user)
        await session.commit()
        await session.refresh(user)


    # ==================================================================================================


    def get_failed_attempts_key(self, email: str) -> str:
        return f"{email}"

    def increment_failed_login(self, email: str):
        key = self.get_failed_attempts_key(email)
        r.incr(key)
        r.expire(key, BLOCK_DURATION_SECONDS)

    def reset_failed_login(self, email: str):
        key = self.get_failed_attempts_key(email)
        r.delete(key)

    def is_user_blocked(self, email: str) -> bool:
        key = self.get_failed_attempts_key(email)
        attempts = int(r.get(key) or 0)
        return attempts >= MAX_FAILED_ATTEMPTS