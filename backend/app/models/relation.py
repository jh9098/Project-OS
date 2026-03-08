import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import RelationTypeEnum


class ProjectRelation(Base):
    __tablename__ = 'project_relations'
    __table_args__ = (
        UniqueConstraint('source_project_id', 'target_project_id', 'relation_type', name='uq_project_relation_unique'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    target_project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, default=RelationTypeEnum.RELATED_TO.value)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    source_project = relationship('Project', back_populates='outgoing_relations', foreign_keys=[source_project_id])
    target_project = relationship('Project', back_populates='incoming_relations', foreign_keys=[target_project_id])
