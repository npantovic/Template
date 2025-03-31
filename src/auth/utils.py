import uuid
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from starlette.templating import Jinja2Templates
from src.config import *
import logging
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

ACCESS_TOKEN_EXPIRE = 43200

# ===============================================================================

password_context = CryptContext(
    schemes=["bcrypt"]
)

def generate_password_hash(password: str) -> str:
    hash = password_context.hash(password)

    return hash

def verify_password_hash(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)

# ===============================================================================

def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    payload = {}

    payload['user'] = user_data
    payload['exp'] = datetime.now() + (expiry if expiry is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRE))
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = refresh

    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM,
    )

    return token


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt = token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )

        return token_data

    except jwt.PyJWTError as e:
        logging.exception(e)
        return None


# ===============================================================================

templates = Jinja2Templates(directory="src/templates")

serializer = URLSafeTimedSerializer(
    secret_key=Config.JWT_SECRET,
    salt="email-configuration"
)


def create_url_safe_token(data: dict):
    expiration_time = timedelta(minutes=1)
    data["exp"] = (datetime.now() + expiration_time).isoformat()
    token = serializer.dumps(data)
    return token


def decode_url_safe_token(token: str):
    try:
        token_data = serializer.loads(token, max_age=3600)
        return token_data
    except SignatureExpired:
        raise HTTPException(status_code=400, detail="Verification link has expired.")
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid verification token.")
    except Exception as e:
        logging.exception(str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")





