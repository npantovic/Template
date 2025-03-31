from fastapi import APIRouter, status, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from typing import List
from fastapi.exceptions import HTTPException
from .serializers import UserCreateSerializer, UserSerializer, UserLoginSerializer
from .model import User
from .service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db.main import get_session
from ..db.redis import add_jti_to_blocklist
from .dependencies import AccessTokenBearer
from .utils import decode_token, create_access_token, verify_password_hash, decode_url_safe_token, create_url_safe_token
from datetime import timedelta
from starlette.templating import Jinja2Templates
from src.config import Config
from ..mail import create_message, mail

REFRESH_TOKEN_EXPIRY = 2

auth_router = APIRouter()
user_service = UserService()
access_token_bearer = AccessTokenBearer()
templates = Jinja2Templates(directory="src/templates")


@auth_router.post("/all_users", response_model=List[User])
async def get_all_users(session: AsyncSession = Depends(get_session),): # user_details = Depends(access_token_bearer)
    # role = user_details.get('user', {}).get("role")
    role = "admin"
    if role == "admin":
        users = await user_service.get_all_users(session)
        return users
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not allowed")


@auth_router.post("/singup", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateSerializer, bg_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    email = user_data.email
    username = user_data.username
    ucin = user_data.UCIN

    user_exists = await user_service.user_exists(email, username, ucin, session)

    if user_exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists, email, username or UCIN is already taken")

    new_user = await user_service.create_user(user_data, session)

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"

    html_message = f"""
            <h1>Verify your Email</h1>
            <p>Please verify your account. <a href="{link}">Verify here</a> </p>
            """

    message = create_message(
        recipients=[email],
        subject="Verify your Email",
        body=html_message,
    )

    bg_tasks.add_task(mail.send_message, message)

    return {
        "message": "Account verification email sent",
        "user": new_user
    }

    # return new_user


@auth_router.post('/login')
async def login_users(login_data: UserLoginSerializer, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password_hash = login_data.password_hash

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        if user.is_verified:
            password_valid = verify_password_hash(password_hash, user.password_hash)
            if password_valid:
                access_token = create_access_token(
                    user_data={
                        'email': user.email,
                        "user_uid": str(user.uid),
                        "role": user.role,
                    }
                )

                refresh_token = create_access_token(
                    user_data={
                        'email': user.email,
                        "user_uid": str(user.uid),
                        "role": user.role,
                    },
                    refresh=True,
                    expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
                )

                return JSONResponse(
                    content={
                        "message": "Successfully logged in",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user" : {
                            "email": user.email,
                            "uid": str(user.uid),
                            "role": user.role,
                        }
                    }
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not verified, check your email",
            )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid email or password",
    )

@auth_router.get('/verify/{token}', response_class=HTMLResponse, include_in_schema=False)
async def verify_user_account(token: str, request: Request, session: AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)

    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await user_service.update_user_email_verify(user, {"is_verified": True}, session)

        return templates.TemplateResponse("verify_account.html", {
            "request": request,
            "title": "Account Verified",
            "message": "Account Verified Successfully",
            "details": "Your account has been successfully verified. You can now log in."
        })

    return templates.TemplateResponse("verify_account.html", {
        "request": request,
        "title": "Account Verification Failed",
        "message": "Account Not Verified",
        "details": "Sorry, there was an issue verifying your account."
    })


@auth_router.get('/logout')
async def logout(token_details: dict = Depends(AccessTokenBearer())):

    jti = token_details['jti']

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={
            "message": "Successfully logged out"
        },
        status_code=status.HTTP_200_OK
    )