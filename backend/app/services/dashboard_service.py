from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.task import Task
from app.utils.enums import PriorityEnum, ProjectStatusEnum, TaskStatusEnum


class DashboardService:
    @staticmethod
    def get_summary(db: Session) -> dict:
        total = db.scalar(select(func.count()).select_from(Project)) or 0
        developing = db.scalar(select(func.count()).select_from(Project).where(Project.status == ProjectStatusEnum.DEVELOPING.value)) or 0
        active = db.scalar(select(func.count()).select_from(Project).where(Project.status == ProjectStatusEnum.ACTIVE.value)) or 0
        paused = db.scalar(select(func.count()).select_from(Project).where(Project.status == ProjectStatusEnum.PAUSED.value)) or 0
        blocked = db.scalar(select(func.count()).select_from(Project).where(Project.blocker.is_not(None), Project.blocker != '')) or 0

        today_focus_tasks = db.scalars(
            select(Task)
            .options(joinedload(Task.project))
            .where(Task.is_today_focus.is_(True), Task.task_status != TaskStatusEnum.DONE.value)
            .order_by(Task.updated_at.desc())
            .limit(10)
        ).unique().all()

        recent_projects = db.scalars(select(Project).order_by(Project.updated_at.desc()).limit(10)).all()
        blocked_projects = db.scalars(
            select(Project)
            .where(Project.blocker.is_not(None), Project.blocker != '')
            .order_by(Project.updated_at.desc())
            .limit(10)
        ).all()
        high_priority_projects = db.scalars(
            select(Project)
            .where(Project.priority.in_([PriorityEnum.CRITICAL.value, PriorityEnum.HIGH.value]))
            .order_by(Project.updated_at.desc())
            .limit(10)
        ).all()

        return {
            'project_counts': {
                'total': total,
                'developing': developing,
                'active': active,
                'paused': paused,
                'blocked': blocked,
            },
            'today_focus_tasks': today_focus_tasks,
            'recent_projects': recent_projects,
            'blocked_projects': blocked_projects,
            'high_priority_projects': high_priority_projects,
        }
