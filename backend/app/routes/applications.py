"""Applications API routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import Application, Scheme, User
from app.schemas.schemas import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, MessageResponse
)

router = APIRouter(prefix="/api/applications", tags=["applications"])

STATUS_DISCLAIMER = (
    "Note: 'Applied' and 'Completed' statuses reflect only what you have self-reported. "
    "JanMitra does not have access to official government application systems "
    "and cannot verify your actual application status."
)


@router.get("", response_model=List[ApplicationResponse])
def get_applications(user_id: int, db: Session = Depends(get_db)):
    apps = (
        db.query(Application)
        .options(joinedload(Application.scheme))
        .filter(Application.user_id == user_id)
        .order_by(Application.updated_at.desc())
        .all()
    )
    return apps


@router.post("", response_model=ApplicationResponse, status_code=201)
def create_application(
    user_id: int,
    data: ApplicationCreate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    scheme = db.query(Scheme).filter(Scheme.id == data.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    existing = (
        db.query(Application)
        .filter(Application.user_id == user_id, Application.scheme_id == data.scheme_id)
        .first()
    )
    if existing:
        return existing

    app = Application(user_id=user_id, **data.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    user_id: int,
    data: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    app = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}", response_model=MessageResponse)
def delete_application(
    application_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    app = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
    return {"message": "Application removed"}
