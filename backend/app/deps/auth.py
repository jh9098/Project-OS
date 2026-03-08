from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User

security_scheme = HTTPBearer(auto_error=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
    )
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
        if not user_id:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.get(User, user_id)
    if not user:
        raise credentials_exception
    return user
