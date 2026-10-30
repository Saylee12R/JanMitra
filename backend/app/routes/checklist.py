"""Checklist API routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import ChecklistItem, Scheme, User
from app.schemas.schemas import (
    ChecklistItemCreate, ChecklistItemUpdate,
    ChecklistItemResponse, ChecklistResponse, MessageResponse,
)

router = APIRouter(prefix="/api/checklist", tags=["checklist"])


def _scheme_default_checklist(scheme: Scheme) -> List[dict]:
    """Generate default checklist from scheme's documents list."""
    items = []
    if scheme.documents:
        for i, doc in enumerate(scheme.documents):
            items.append({"title": doc, "description": None, "order": i})
    return items


@router.get("/{scheme_id}", response_model=ChecklistResponse)
def get_checklist(scheme_id: int, user_id: int, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.scheme_id == scheme_id, ChecklistItem.user_id == user_id)
        .order_by(ChecklistItem.order.asc())
        .all()
    )

    # Auto-populate from scheme documents if empty
    if not items and scheme.documents:
        for i, doc in enumerate(scheme.documents):
            item = ChecklistItem(
                scheme_id=scheme_id,
                user_id=user_id,
                title=doc,
                order=i,
            )
            db.add(item)
        db.commit()
        items = (
            db.query(ChecklistItem)
            .filter(ChecklistItem.scheme_id == scheme_id, ChecklistItem.user_id == user_id)
            .order_by(ChecklistItem.order.asc())
            .all()
        )

    total = len(items)
    completed_count = sum(1 for i in items if i.completed)
    progress = round((completed_count / total) * 100, 1) if total > 0 else 0.0

    return ChecklistResponse(
        scheme_id=scheme_id,
        total=total,
        completed=completed_count,
        progress_percent=progress,
        items=items,
    )


@router.post("/{scheme_id}", response_model=ChecklistItemResponse, status_code=201)
def add_checklist_item(
    scheme_id: int,
    user_id: int,
    data: ChecklistItemCreate,
    db: Session = Depends(get_db),
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    item = ChecklistItem(
        scheme_id=scheme_id,
        user_id=user_id,
        **data.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ChecklistItemResponse)
def update_checklist_item(
    item_id: int,
    user_id: int,
    data: ChecklistItemUpdate,
    db: Session = Depends(get_db),
):
    item = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.id == item_id, ChecklistItem.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", response_model=MessageResponse)
def delete_checklist_item(
    item_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.id == item_id, ChecklistItem.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    db.delete(item)
    db.commit()
    return {"message": "Checklist item deleted"}
