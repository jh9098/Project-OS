import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import PriorityEnum, TaskStatusEnum


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_status: Mapped[str] = mapped_column(String(50), nullable=False, default=TaskStatusEnum.TODO.value)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default=PriorityEnum.MEDIUM.value)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_today_focus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocker: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship('Project', back_populates='tasks')
