from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase
from app.utils.enums import PriorityEnum, TaskStatusEnum


class TaskBase(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    task_status: TaskStatusEnum = TaskStatusEnum.TODO
    priority: PriorityEnum = PriorityEnum.MEDIUM
    due_date: date | None = None
    is_today_focus: bool = False
    blocker: str | None = Field(default=None, max_length=300)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    task_status: TaskStatusEnum | None = None
    priority: PriorityEnum | None = None
    due_date: date | None = None
    is_today_focus: bool | None = None
    blocker: str | None = Field(default=None, max_length=300)


class TaskProjectBrief(ORMBase):
    id: str
    name: str
    slug: str


class TaskResponse(ORMBase):
    id: str
    project_id: str
    title: str
    description: str | None = None
    task_status: str
    priority: str
    due_date: date | None = None
    is_today_focus: bool
    blocker: str | None = None
    created_at: datetime
    updated_at: datetime
    project: TaskProjectBrief | None = None


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    limit: int
