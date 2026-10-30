"""Schemes API routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models.models import Scheme
from app.schemas.schemas import SchemeResponse, SchemeListResponse, CompareRequest, CompareResponse

router = APIRouter(prefix="/api/schemes", tags=["schemes"])


@router.get("", response_model=List[SchemeListResponse])
def list_schemes(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None),
    ministry: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    max_income: Optional[float] = Query(None),
    occupation: Optional[str] = Query(None),
    sort: Optional[str] = Query("relevance", enum=["relevance", "newest", "alphabetical", "category"]),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Scheme).filter(Scheme.active == True)

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Scheme.name.ilike(search),
                Scheme.description.ilike(search),
                Scheme.ministry.ilike(search),
                Scheme.category.ilike(search),
            )
        )

    if category:
        query = query.filter(Scheme.category.ilike(f"%{category}%"))

    if ministry:
        query = query.filter(Scheme.ministry.ilike(f"%{ministry}%"))

    if gender and gender.lower() not in ("any", "all"):
        query = query.filter(
            or_(
                Scheme.gender == None,
                Scheme.gender.ilike("any"),
                Scheme.gender.ilike("all"),
                Scheme.gender.ilike(gender),
            )
        )

    if max_income is not None:
        query = query.filter(
            or_(
                Scheme.income_limit == None,
                Scheme.income_limit >= max_income,
            )
        )

    # Sorting
    if sort == "newest":
        query = query.order_by(Scheme.created_at.desc())
    elif sort == "alphabetical":
        query = query.order_by(Scheme.name.asc())
    elif sort == "category":
        query = query.order_by(Scheme.category.asc(), Scheme.name.asc())
    else:
        query = query.order_by(Scheme.id.asc())

    schemes = query.offset(offset).limit(limit).all()
    return schemes


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(scheme_id: int, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id, Scheme.active == True).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme


@router.get("/slug/{slug}", response_model=SchemeResponse)
def get_scheme_by_slug(slug: str, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.slug == slug, Scheme.active == True).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme
