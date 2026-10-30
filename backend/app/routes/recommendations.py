"""Recommendations API route"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Scheme, User
from app.schemas.schemas import UserProfileInput, RecommendationResponse
from app.services.eligibility import get_recommendations, compute_profile_completeness

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post("/recommend", response_model=RecommendationResponse)
def recommend_schemes(
    profile: UserProfileInput,
    db: Session = Depends(get_db),
):
    """
    Match government schemes to user profile using deterministic eligibility rules.

    DISCLAIMER: Results indicate potential eligibility, not guaranteed eligibility.
    Final eligibility must be confirmed with the official scheme authority.
    """
    active_schemes = db.query(Scheme).filter(Scheme.active == True).all()

    if not active_schemes:
        return RecommendationResponse(
            count=0,
            profile_completeness=compute_profile_completeness(profile),
            schemes=[],
        )

    recommendations = get_recommendations(active_schemes, profile)
    completeness = compute_profile_completeness(profile)

    return RecommendationResponse(
        count=len(recommendations),
        profile_completeness=completeness,
        schemes=recommendations,
    )
