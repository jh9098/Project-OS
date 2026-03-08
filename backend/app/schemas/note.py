from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase
from app.utils.enums import NoteTypeEnum


class NoteBase(BaseModel):
    project_id: str
    note_type: NoteTypeEnum
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    note_type: NoteTypeEnum | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)


class NoteProjectBrief(ORMBase):
    id: str
    name: str
    slug: str


class NoteResponse(ORMBase):
    id: str
    project_id: str
    note_type: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    project: NoteProjectBrief | None = None


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    limit: int
