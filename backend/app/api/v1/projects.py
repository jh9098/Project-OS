from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix='/projects', tags=['projects'])


@router.get('', response_model=ProjectListResponse)
def list_projects(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias='status'),
    project_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    monetization_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = ProjectService.list(
        db,
        q=q,
        status=status_filter,
        project_type=project_type,
        priority=priority,
        monetization_type=monetization_type,
        page=page,
        limit=limit,
    )
    return ProjectListResponse(items=items, total=total, page=page, limit=limit)


@router.post('', response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return ProjectService.create(db, payload)


@router.get('/{project_id}', response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return ProjectService.get_or_404(db, project_id)


@router.patch('/{project_id}', response_model=ProjectResponse)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project = ProjectService.get_or_404(db, project_id)
    return ProjectService.update(db, project, payload)


@router.delete('/{project_id}', response_model=DeleteResponse)
def delete_project(project_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    project = ProjectService.get_or_404(db, project_id)
    ProjectService.delete(db, project)
    return DeleteResponse(ok=True)
