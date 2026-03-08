from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.note import Note
from app.models.project import Project
from app.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    @staticmethod
    def create(db: Session, payload: NoteCreate) -> Note:
        project = db.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
        note = Note(**payload.model_dump())
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def list(
        db: Session,
        *,
        q: str | None,
        project_id: str | None,
        note_type: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Note], int]:
        stmt = select(Note).options(joinedload(Note.project))
        count_stmt = select(func.count()).select_from(Note)

        filters: list[Any] = []
        if q:
            like = f'%{q.strip()}%'
            filters.append(or_(Note.title.ilike(like), Note.content.ilike(like)))
        if project_id:
            filters.append(Note.project_id == project_id)
        if note_type:
            filters.append(Note.note_type == note_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = db.scalar(count_stmt) or 0
        items = db.scalars(
            stmt.order_by(Note.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        ).unique().all()
        return items, total

    @staticmethod
    def get_or_404(db: Session, note_id: str) -> Note:
        stmt = select(Note).options(joinedload(Note.project)).where(Note.id == note_id)
        note = db.scalar(stmt)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Note not found')
        return note

    @staticmethod
    def update(db: Session, note: Note, payload: NoteUpdate) -> Note:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(note, key, value)
        db.add(note)
        db.commit()
        db.refresh(note)
        return NoteService.get_or_404(db, note.id)

    @staticmethod
    def delete(db: Session, note: Note) -> None:
        db.delete(note)
        db.commit()
