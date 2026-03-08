from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase
from app.utils.enums import RelationTypeEnum


class RelationBase(BaseModel):
    source_project_id: str
    target_project_id: str
    relation_type: RelationTypeEnum
    description: str | None = Field(default=None, max_length=300)


class RelationCreate(RelationBase):
    pass


class ProjectBrief(ORMBase):
    id: str
    name: str
    slug: str
    status: str
    priority: str


class RelationResponse(ORMBase):
    id: str
    source_project_id: str
    target_project_id: str
    relation_type: str
    description: str | None = None
    created_at: datetime
    source_project: ProjectBrief
    target_project: ProjectBrief


class RelationListResponse(BaseModel):
    items: list[RelationResponse]
    total: int
    page: int
    limit: int
