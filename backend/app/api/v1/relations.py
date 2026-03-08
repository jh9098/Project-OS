from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse
from app.schemas.relation import RelationCreate, RelationListResponse, RelationResponse
from app.services.relation_service import RelationService

router = APIRouter(prefix='/relations', tags=['relations'])


@router.get('', response_model=RelationListResponse)
def list_relations(
    project_id: str | None = Query(default=None),
    relation_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = RelationService.list(
        db,
        project_id=project_id,
        relation_type=relation_type,
        page=page,
        limit=limit,
    )
    return RelationListResponse(items=items, total=total, page=page, limit=limit)


@router.post('', response_model=RelationResponse, status_code=status.HTTP_201_CREATED)
def create_relation(payload: RelationCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return RelationService.create(db, payload)


@router.delete('/{relation_id}', response_model=DeleteResponse)
def delete_relation(relation_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    relation = RelationService.get_or_404(db, relation_id)
    RelationService.delete(db, relation)
    return DeleteResponse(ok=True)
