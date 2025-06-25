from passlib.context import CryptContext
from datetime import timedelta, datetime
import jwt
from config import settings
import uuid
import logging

passwd_context = CryptContext(schemes=["bcrypt"])
ACCESS_TOKEN_EXPIRY = 3600

def generate_passwd_hash(password: str) -> str:
    return passwd_context.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return passwd_context.verify(password, hash)

def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    payload = {}
    payload["user"] = user_data
    payload["jti"] = str(uuid.uuid4())  
    payload["refresh"] = refresh

   
    token = jwt.encode(
        payload=payload,
        key=settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    return token

def decode_token(token: str) -> dict:
    try:
        # Decode the token
        token_data = jwt.decode(
            jwt=token,
            key=settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]  # Ensure this is a list
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None