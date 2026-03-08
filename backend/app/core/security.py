from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
# NOTE:
# - bcrypt has a 72-byte password input limit and may fail on newer Python/runtime
#   combos when backend packages are mismatched.
# - pbkdf2_sha256 avoids that hard length limit and is fully supported by passlib.
pwd_context = CryptContext(schemes=['pbkdf2_sha256', 'bcrypt'], deprecated='auto')
ALGORITHM = 'HS256'


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
