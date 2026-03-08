from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.enums import TaskStatusEnum


class TaskService:
    @staticmethod
    def create(db: Session, payload: TaskCreate) -> Task:
        project = db.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
        task = Task(**payload.model_dump())
        if task.task_status == TaskStatusEnum.DONE.value:
            task.is_today_focus = False
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def list(
        db: Session,
        *,
        q: str | None,
        project_id: str | None,
        task_status: str | None,
        priority: str | None,
        is_today_focus: bool | None,
        page: int,
        limit: int,
    ) -> tuple[list[Task], int]:
        stmt = select(Task).options(joinedload(Task.project))
        count_stmt = select(func.count()).select_from(Task)
        filters: list[Any] = []

        if q:
            like = f'%{q.strip()}%'
            filters.append(or_(Task.title.ilike(like), Task.description.ilike(like)))
        if project_id:
            filters.append(Task.project_id == project_id)
        if task_status:
            filters.append(Task.task_status == task_status)
        if priority:
            filters.append(Task.priority == priority)
        if is_today_focus is not None:
            filters.append(Task.is_today_focus == is_today_focus)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = db.scalar(count_stmt) or 0
        items = db.scalars(
            stmt.order_by(Task.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        ).unique().all()
        return items, total

    @staticmethod
    def get_or_404(db: Session, task_id: str) -> Task:
        stmt = select(Task).options(joinedload(Task.project)).where(Task.id == task_id)
        task = db.scalar(stmt)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
        return task

    @staticmethod
    def update(db: Session, task: Task, payload: TaskUpdate) -> Task:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(task, key, value)
        if task.task_status == TaskStatusEnum.DONE.value:
            task.is_today_focus = False
        db.add(task)
        db.commit()
        db.refresh(task)
        return TaskService.get_or_404(db, task.id)

    @staticmethod
    def delete(db: Session, task: Task) -> None:
        db.delete(task)
        db.commit()
