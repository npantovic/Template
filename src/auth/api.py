from fastapi import APIRouter, status, Depends, Request, BackgroundTasks, Response, Form
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from typing import List
from fastapi.exceptions import HTTPException
from .serializers import UserCreateSerializer, UserLoginSerializer, UsernameChangeSerializer, EmailChangeSerializer, UserLoginSerializerOpt, PasswordResetSerializerNoLogin
from .model import User
from .service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db.main import get_session
from ..db.redis import add_jti_to_blocklist
from .dependencies import AccessTokenBearer
from .utils import (
    generate_password_hash,
    create_access_token,
    verify_password_hash,
    decode_url_safe_token,
    create_url_safe_token
)
from datetime import timedelta
from starlette.templating import Jinja2Templates
from src.config import Config
from ..mail import create_message, mail
from .dependencies import get_current_user

from fastapi.responses import StreamingResponse
import pyotp


REFRESH_TOKEN_EXPIRY = 2

auth_router = APIRouter()
user_service = UserService()
access_token_bearer = AccessTokenBearer()
templates = Jinja2Templates(directory="src/templates")


# =========================================================ALL_USER====================================================================


@auth_router.post("/all_users", response_model=List[User])
async def get_all_users(session: AsyncSession = Depends(get_session)):
    # role = user_details.get('user', {}).get("role")
    role = "admin"
    if role == "admin":
        users = await user_service.get_all_users(session)
        return users
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not allowed")


@auth_router.get('/me')
async def get_curr_user(current_user = Depends(get_current_user)):
    return current_user


# =========================================================CREATE_USER====================================================================


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

    html_message = templates.TemplateResponse(
        "verify_account_mail.html",
        {"request": None, "link": link}
    ).body.decode("utf-8") 

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


@auth_router.post("/singup_admin", response_model=UserCreateSerializer, status_code=status.HTTP_201_CREATED)
async def create_user_admin(user_data: UserCreateSerializer, session: AsyncSession = Depends(get_session)):
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists")

    new_user = await user_service.create_user_admin(user_data, session)

    return new_user

# =========================================================LOGIN_LOGOUT====================================================================


@auth_router.post('/if2falogin')
async def if2falogin_users(login_data: UserLoginSerializerOpt, session: AsyncSession = Depends(get_session)):
    if not login_data.otp_code:
        raise HTTPException(status_code=400, detail="2FA kod je obavezan")

    user = await user_service.get_user_by_email(login_data.email, session)

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(login_data.otp_code, valid_window=1):  # valid_window dozvoljava malo kašnjenje
        # print("===============================")
        # print("Kod koji treba da dobijaš u aplikaciji:", pyotp.TOTP("ECSWTHXWRM3JQILP243FKFQOPZXTVEQO").now())
        # print("===============================")
        raise HTTPException(status_code=401, detail="Neispravan 2FA kod")
    
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
    user_service.reset_failed_login(login_data.email)
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


@auth_router.post('/login')
async def login_users(login_data: UserLoginSerializer, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password_hash = login_data.password_hash

    if user_service.is_user_blocked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="To many failed login attempts, please try again later."
        )

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        if user.is_verified:
            password_valid = verify_password_hash(password_hash, user.password_hash)
            if password_valid:
                if not user.enabled_2fa:
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
                    user_service.reset_failed_login(email)
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
                    return JSONResponse(
                        content={
                            "message": "2FA required",
                            "requires_2fa": True,
                            "email": user.email
                        },
                        status_code=status.HTTP_200_OK
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not verified, check your email",
            )
    user_service.increment_failed_login(email)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid email or password",
    )


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


# =========================================================VERIFY_USER====================================================================


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


# =========================================================UPDATE_DELETE_USER====================================================================


@auth_router.patch("/update-username")
async def update_username(data: UsernameChangeSerializer, session: AsyncSession = Depends(get_session)):
    updated_user = await user_service.update_username(data.user_uid, data.new_username, session)
    return {"message": "Username updated successfully", "user": updated_user}


@auth_router.patch("/update-email")
async def update_email(data: EmailChangeSerializer, session: AsyncSession = Depends(get_session)):
    updated_user = await user_service.update_email(data.user_uid, data.new_email, session)
    return {"message": "Email updated successfully", "user": updated_user}


@auth_router.delete('/delete/{user_uid}')
async def delete_user(user_uid: str, session: AsyncSession = Depends(get_session), user_details = Depends(access_token_bearer)):
    role = user_details.get('user', {}).get("role")
    uid = user_details.get('user', {}).get('user_uid')
    if role == "admin" or user_uid == uid:
        user_to_delete = await user_service.delete_user(user_uid, session)
        if user_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        else:
            return {}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not allowed")


# =========================================================PASSWOR_RESTART====================================================================


@auth_router.post('/password_reset_request')
async def password_reset_request(bg_tasks: BackgroundTasks, user_details=Depends(access_token_bearer)):
    email = user_details.get('user', {}).get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found")


    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password_reset_confirm/{token}"

    html_message = f"""
                    <h1>Reset your password</h1>
                    <p>Please reset your password. <a href="{link}">Reset here</a> </p>
                    """

    message = create_message(
                recipients=[email],
                subject="Reset your password",
                body=html_message,
            )
    
    bg_tasks.add_task(mail.send_message, message)

    return JSONResponse(
        content={
            "message": "Please check your email to reset your password"
        },
        status_code=status.HTTP_200_OK
    )


@auth_router.post('/password_reset_request_no_login')
async def password_reset_request_no_login(user_data: PasswordResetSerializerNoLogin, bg_tasks: BackgroundTasks):
    email = user_data.email

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found")


    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password_reset_confirm/{token}"

    html_message = f"""
                    <h1>Reset your password</h1>
                    <p>Please reset your password. <a href="{link}">Reset here</a> </p>
                    """

    message = create_message(
                recipients=[email],
                subject="Reset your password",
                body=html_message,
            )
    
    bg_tasks.add_task(mail.send_message, message)

    return JSONResponse(
        content={
            "message": "Please check your email to reset your password"
        },
        status_code=status.HTTP_200_OK
    )


@auth_router.get('/password_reset_confirm/{token}', response_class=HTMLResponse, include_in_schema=False)
async def reset_password_page(token: str, request: Request):
    return templates.TemplateResponse("password_reset_form.html", {
        "request": request,
        "token": token,
        "title": "Reset Your Password",
        "details": "Please enter your new password and confirm it."
    })


@auth_router.post('/password_reset_confirm/{token}', include_in_schema=False)
async def reset_user_password(
    request: Request,
    token: str,
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):

    if new_password != confirm_new_password:
        raise HTTPException(
            detail="Passwords don't match",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    await user_service.validate_password_complexity(new_password)

    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        passwd_hash = generate_password_hash(new_password)

        await user_service.update_user_email_verify(user, {"password_hash": passwd_hash}, session)

        # await add_jti_to_blocklist(token_data['jti']) ZA REDIS

        return templates.TemplateResponse("password_reset.html", {
            "request": request,
            "title": "Password Reset",
            "message": "Password Reset Successfully",
            "details": "Your password has been reset.",
        })

    return templates.TemplateResponse("password_reset.html", {
        "request": request,
        "title": "Password Reset Failed",
        "message": "Password Reset Failed",
        "details": "Sorry, there was an issue resetting your password."
    })


# =======================================================2FA=====================================================================


@auth_router.get("/2fa/qr-code/{username}")
async def get_2fa_qr_code(username: str, session: AsyncSession = Depends(get_session)):
    user = await user_service.get_user_by_username(username, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    secret = user_service.generate_secret()

    await user_service.update_totp(user.uid, secret, session)
    await user_service.update_enabled_2fa(user.uid, session)

    img_buf = user_service.get_qr_code(username, secret)
    return StreamingResponse(img_buf, media_type="image/png")


@auth_router.post('/disable_2fa')
async def disable_2fa(user_details=Depends(access_token_bearer), session: AsyncSession = Depends(get_session)):
    email = user_details.get('user', {}).get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found")

    user = await user_service.get_user_by_email(email, session)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await user_service.deactivate_2FA(email, session)

    return JSONResponse(
        content={
            "message": "2FA has been disabled successfully",
            "user": {
                "email": user.email,
                "enabled_2fa": user.enabled_2fa
            }
        },
        status_code=status.HTTP_200_OK
    )


# ====================================================CHAT================================================================


import requests
rasa_router = APIRouter()

RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"

@auth_router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})