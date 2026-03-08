from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse
from app.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate
from app.services.note_service import NoteService

router = APIRouter(prefix='/notes', tags=['notes'])


@router.get('', response_model=NoteListResponse)
def list_notes(
    q: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    note_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = NoteService.list(
        db,
        q=q,
        project_id=project_id,
        note_type=note_type,
        page=page,
        limit=limit,
    )
    return NoteListResponse(items=items, total=total, page=page, limit=limit)


@router.post('', response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return NoteService.create(db, payload)


@router.get('/{note_id}', response_model=NoteResponse)
def get_note(note_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return NoteService.get_or_404(db, note_id)


@router.patch('/{note_id}', response_model=NoteResponse)
def update_note(note_id: str, payload: NoteUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    note = NoteService.get_or_404(db, note_id)
    return NoteService.update(db, note, payload)


@router.delete('/{note_id}', response_model=DeleteResponse)
def delete_note(note_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    note = NoteService.get_or_404(db, note_id)
    NoteService.delete(db, note)
    return DeleteResponse(ok=True)
