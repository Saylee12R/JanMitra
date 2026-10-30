"""Saved Schemes API routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import SavedScheme, Scheme, User
from app.schemas.schemas import SavedSchemeResponse, MessageResponse

router = APIRouter(prefix="/api/saved", tags=["saved"])


def _get_user(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("", response_model=List[SavedSchemeResponse])
def get_saved_schemes(user_id: int, db: Session = Depends(get_db)):
    _get_user(user_id, db)
    saved = (
        db.query(SavedScheme)
        .options(joinedload(SavedScheme.scheme))
        .filter(SavedScheme.user_id == user_id)
        .order_by(SavedScheme.created_at.desc())
        .all()
    )
    return saved


@router.post("/{scheme_id}", response_model=SavedSchemeResponse, status_code=201)
def save_scheme(scheme_id: int, user_id: int, db: Session = Depends(get_db)):
    _get_user(user_id, db)
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    existing = (
        db.query(SavedScheme)
        .filter(SavedScheme.user_id == user_id, SavedScheme.scheme_id == scheme_id)
        .first()
    )
    if existing:
        return existing

    saved = SavedScheme(user_id=user_id, scheme_id=scheme_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.delete("/{scheme_id}", response_model=MessageResponse)
def remove_saved_scheme(scheme_id: int, user_id: int, db: Session = Depends(get_db)):
    saved = (
        db.query(SavedScheme)
        .filter(SavedScheme.user_id == user_id, SavedScheme.scheme_id == scheme_id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Scheme not saved")
    db.delete(saved)
    db.commit()
    return {"message": "Scheme removed from saved list"}
