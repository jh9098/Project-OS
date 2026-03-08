from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.slug import slugify


class ProjectService:
    @staticmethod
    def _generate_unique_slug(db: Session, name: str, desired_slug: str | None = None, exclude_id: str | None = None) -> str:
        base_slug = slugify(desired_slug or name)
        slug = base_slug
        counter = 1
        while True:
            stmt = select(Project).where(Project.slug == slug)
            if exclude_id:
                stmt = stmt.where(Project.id != exclude_id)
            existing = db.scalar(stmt)
            if not existing:
                return slug
            counter += 1
            slug = f'{base_slug}-{counter}'

    @staticmethod
    def create(db: Session, payload: ProjectCreate) -> Project:
        project = Project(**payload.model_dump(exclude={'slug'}))
        project.slug = ProjectService._generate_unique_slug(db, name=payload.name, desired_slug=payload.slug)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def list(
        db: Session,
        *,
        q: str | None,
        status: str | None,
        project_type: str | None,
        priority: str | None,
        monetization_type: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Project], int]:
        stmt = select(Project)
        count_stmt = select(func.count()).select_from(Project)

        filters: list[Any] = []
        if q:
            like = f'%{q.strip()}%'
            filters.append(
                or_(
                    Project.name.ilike(like),
                    Project.summary.ilike(like),
                    Project.description.ilike(like),
                    Project.next_action.ilike(like),
                )
            )
        if status:
            filters.append(Project.status == status)
        if project_type:
            filters.append(Project.project_type == project_type)
        if priority:
            filters.append(Project.priority == priority)
        if monetization_type:
            filters.append(Project.monetization_type == monetization_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = db.scalar(count_stmt) or 0
        items = db.scalars(
            stmt.order_by(Project.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        ).all()
        return items, total

    @staticmethod
    def get_or_404(db: Session, project_id: str) -> Project:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
        return project

    @staticmethod
    def update(db: Session, project: Project, payload: ProjectUpdate) -> Project:
        data = payload.model_dump(exclude_unset=True)
        if 'slug' in data or 'name' in data:
            desired_slug = data.get('slug', project.slug)
            desired_name = data.get('name', project.name)
            project.slug = ProjectService._generate_unique_slug(
                db,
                name=desired_name,
                desired_slug=desired_slug,
                exclude_id=project.id,
            )
            data.pop('slug', None)
        for key, value in data.items():
            setattr(project, key, value)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, project: Project) -> None:
        db.delete(project)
        db.commit()
