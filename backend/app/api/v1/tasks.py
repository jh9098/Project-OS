from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('', response_model=TaskListResponse)
def list_tasks(
    q: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    task_status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    is_today_focus: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = TaskService.list(
        db,
        q=q,
        project_id=project_id,
        task_status=task_status,
        priority=priority,
        is_today_focus=is_today_focus,
        page=page,
        limit=limit,
    )
    return TaskListResponse(items=items, total=total, page=page, limit=limit)


@router.post('', response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return TaskService.create(db, payload)


@router.get('/{task_id}', response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return TaskService.get_or_404(db, task_id)


@router.patch('/{task_id}', response_model=TaskResponse)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    task = TaskService.get_or_404(db, task_id)
    return TaskService.update(db, task, payload)


@router.delete('/{task_id}', response_model=DeleteResponse)
def delete_task(task_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    task = TaskService.get_or_404(db, task_id)
    TaskService.delete(db, task)
    return DeleteResponse(ok=True)
