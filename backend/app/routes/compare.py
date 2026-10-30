"""Compare schemes API route"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Scheme
from app.schemas.schemas import CompareRequest, CompareResponse, SchemeResponse

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
def compare_schemes(data: CompareRequest, db: Session = Depends(get_db)):
    if len(data.scheme_ids) < 2 or len(data.scheme_ids) > 3:
        raise HTTPException(
            status_code=400, detail="Please select 2 or 3 schemes to compare"
        )

    schemes = db.query(Scheme).filter(Scheme.id.in_(data.scheme_ids)).all()

    if len(schemes) != len(data.scheme_ids):
        raise HTTPException(status_code=404, detail="One or more schemes not found")

    # Return in requested order
    scheme_map = {s.id: s for s in schemes}
    ordered = [scheme_map[sid] for sid in data.scheme_ids if sid in scheme_map]

    return CompareResponse(schemes=ordered)
