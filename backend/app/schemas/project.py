from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase
from app.utils.enums import DomainTypeEnum, MonetizationTypeEnum, PriorityEnum, ProjectStatusEnum, ProjectTypeEnum


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    summary: str = Field(min_length=1, max_length=300)
    description: str | None = None
    project_type: ProjectTypeEnum
    domain_type: DomainTypeEnum
    status: ProjectStatusEnum
    priority: PriorityEnum
    monetization_type: MonetizationTypeEnum
    current_focus: str | None = Field(default=None, max_length=300)
    next_action: str | None = Field(default=None, max_length=300)
    blocker: str | None = Field(default=None, max_length=300)
    frontend_repo_url: str | None = Field(default=None, max_length=500)
    backend_repo_url: str | None = Field(default=None, max_length=500)
    deploy_url: str | None = Field(default=None, max_length=500)
    admin_url: str | None = Field(default=None, max_length=500)
    local_path: str | None = Field(default=None, max_length=500)
    docs_url: str | None = Field(default=None, max_length=500)
    started_at: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    summary: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    project_type: ProjectTypeEnum | None = None
    domain_type: DomainTypeEnum | None = None
    status: ProjectStatusEnum | None = None
    priority: PriorityEnum | None = None
    monetization_type: MonetizationTypeEnum | None = None
    current_focus: str | None = Field(default=None, max_length=300)
    next_action: str | None = Field(default=None, max_length=300)
    blocker: str | None = Field(default=None, max_length=300)
    frontend_repo_url: str | None = Field(default=None, max_length=500)
    backend_repo_url: str | None = Field(default=None, max_length=500)
    deploy_url: str | None = Field(default=None, max_length=500)
    admin_url: str | None = Field(default=None, max_length=500)
    local_path: str | None = Field(default=None, max_length=500)
    docs_url: str | None = Field(default=None, max_length=500)
    started_at: date | None = None


class ProjectResponse(ORMBase):
    id: str
    name: str
    slug: str
    summary: str
    description: str | None = None
    project_type: str
    domain_type: str
    status: str
    priority: str
    monetization_type: str
    current_focus: str | None = None
    next_action: str | None = None
    blocker: str | None = None
    frontend_repo_url: str | None = None
    backend_repo_url: str | None = None
    deploy_url: str | None = None
    admin_url: str | None = None
    local_path: str | None = None
    docs_url: str | None = None
    started_at: date | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    limit: int
