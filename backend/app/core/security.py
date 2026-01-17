from datetime import datetime, timedelta, timezone
import re
import secrets
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_SYMBOL_REGEX = re.compile(r"[^A-Za-z0-9]")
_UPPER_REGEX = re.compile(r"[A-Z]")
_LOWER_REGEX = re.compile(r"[a-z]")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    settings = get_settings()
    expires = expires_minutes or settings.jwt_expire_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expires)
    payload = {"sub": subject, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def validate_password_strength(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password too long (max 72 bytes).")

    if not _LOWER_REGEX.search(password):
        raise ValueError("Password must include a lowercase letter.")
    if not _UPPER_REGEX.search(password):
        raise ValueError("Password must include an uppercase letter.")
    if not _SYMBOL_REGEX.search(password):
        raise ValueError("Password must include a symbol.")

    return password


def generate_token() -> str:
    return secrets.token_urlsafe(32)