from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserMe

settings = get_settings()


class AuthService:
    @staticmethod
    def login(db: Session, username: str, password: str) -> TokenResponse:
        user = db.scalar(select(User).where(User.username == username))
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')

        token = create_access_token(subject=user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        return TokenResponse(
            access_token=token,
            user=UserMe(id=user.id, username=user.username, role=user.role),
        )
