from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, payload.username, payload.password)


@router.get('/me', response_model=UserMe)
def me(current_user: User = Depends(get_current_user)):
    return UserMe(id=current_user.id, username=current_user.username, role=current_user.role)
