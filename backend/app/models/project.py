import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import DomainTypeEnum, MonetizationTypeEnum, PriorityEnum, ProjectStatusEnum, ProjectTypeEnum


class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False, default=ProjectTypeEnum.WEB.value)
    domain_type: Mapped[str] = mapped_column(String(50), nullable=False, default=DomainTypeEnum.OTHER.value)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ProjectStatusEnum.IDEA.value)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default=PriorityEnum.MEDIUM.value)
    monetization_type: Mapped[str] = mapped_column(String(50), nullable=False, default=MonetizationTypeEnum.INTERNAL.value)
    current_focus: Mapped[str | None] = mapped_column(String(300), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(300), nullable=True)
    blocker: Mapped[str | None] = mapped_column(String(300), nullable=True)
    frontend_repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    backend_repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deploy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    admin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    docs_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tasks = relationship('Task', back_populates='project', cascade='all, delete-orphan')
    notes = relationship('Note', back_populates='project', cascade='all, delete-orphan')
    outgoing_relations = relationship(
        'ProjectRelation',
        back_populates='source_project',
        foreign_keys='ProjectRelation.source_project_id',
        cascade='all, delete-orphan',
    )
    incoming_relations = relationship(
        'ProjectRelation',
        back_populates='target_project',
        foreign_keys='ProjectRelation.target_project_id',
        cascade='all, delete-orphan',
    )
