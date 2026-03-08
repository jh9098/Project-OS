from pydantic import BaseModel

from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse


class ProjectCounts(BaseModel):
    total: int
    developing: int
    active: int
    paused: int
    blocked: int


class DashboardSummaryResponse(BaseModel):
    project_counts: ProjectCounts
    today_focus_tasks: list[TaskResponse]
    recent_projects: list[ProjectResponse]
    blocked_projects: list[ProjectResponse]
    high_priority_projects: list[ProjectResponse]
