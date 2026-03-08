from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/summary', response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return DashboardService.get_summary(db)
