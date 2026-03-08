import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import NoteTypeEnum


class Note(Base):
    __tablename__ = 'notes'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    note_type: Mapped[str] = mapped_column(String(50), nullable=False, default=NoteTypeEnum.LOG.value)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship('Project', back_populates='notes')
