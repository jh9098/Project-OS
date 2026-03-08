from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.relation import ProjectRelation
from app.schemas.relation import RelationCreate


class RelationService:
    @staticmethod
    def create(db: Session, payload: RelationCreate) -> ProjectRelation:
        if payload.source_project_id == payload.target_project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='A project cannot relate to itself')

        source = db.get(Project, payload.source_project_id)
        target = db.get(Project, payload.target_project_id)
        if not source or not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Source or target project not found')

        existing = db.scalar(
            select(ProjectRelation).where(
                ProjectRelation.source_project_id == payload.source_project_id,
                ProjectRelation.target_project_id == payload.target_project_id,
                ProjectRelation.relation_type == payload.relation_type.value,
            )
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Relation already exists')

        relation = ProjectRelation(**payload.model_dump())
        db.add(relation)
        db.commit()
        db.refresh(relation)
        return RelationService.get_or_404(db, relation.id)

    @staticmethod
    def list(
        db: Session,
        *,
        project_id: str | None,
        relation_type: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[ProjectRelation], int]:
        stmt = select(ProjectRelation).options(
            joinedload(ProjectRelation.source_project), joinedload(ProjectRelation.target_project)
        )
        count_stmt = select(func.count()).select_from(ProjectRelation)

        filters: list[Any] = []
        if project_id:
            filters.append(
                or_(
                    ProjectRelation.source_project_id == project_id,
                    ProjectRelation.target_project_id == project_id,
                )
            )
        if relation_type:
            filters.append(ProjectRelation.relation_type == relation_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = db.scalar(count_stmt) or 0
        items = db.scalars(
            stmt.order_by(ProjectRelation.created_at.desc()).offset((page - 1) * limit).limit(limit)
        ).unique().all()
        return items, total

    @staticmethod
    def get_or_404(db: Session, relation_id: str) -> ProjectRelation:
        stmt = select(ProjectRelation).options(
            joinedload(ProjectRelation.source_project), joinedload(ProjectRelation.target_project)
        ).where(ProjectRelation.id == relation_id)
        relation = db.scalar(stmt)
        if not relation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Relation not found')
        return relation

    @staticmethod
    def delete(db: Session, relation: ProjectRelation) -> None:
        db.delete(relation)
        db.commit()
