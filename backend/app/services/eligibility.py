"""
JanMitra – Deterministic Eligibility Engine

This engine uses structured eligibility rules to match users to schemes.
It does NOT use an LLM for eligibility decisions.
The LLM is used only for:
  - generating human-readable explanations
  - ranking assistance
  - conversational Q&A

IMPORTANT DISCLAIMER:
  "Based on the information you provided, you may be eligible."
  Final eligibility should be confirmed with the official scheme authority.
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import Scheme, User
from app.schemas.schemas import UserProfileInput, RecommendationItem


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip().lower()


def _check_age(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if profile.age is None:
        return True, None  # can't rule out
    if scheme.min_age is not None and profile.age < scheme.min_age:
        return False, f"Minimum age is {scheme.min_age}"
    if scheme.max_age is not None and profile.age > scheme.max_age:
        return False, f"Maximum age is {scheme.max_age}"
    if scheme.min_age is not None or scheme.max_age is not None:
        return True, "Your age falls within the scheme's eligible age range"
    return True, None


def _check_gender(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if scheme.gender is None or scheme.gender.lower() in ("any", "all", ""):
        return True, None
    if profile.gender is None:
        return True, None
    if _normalize(scheme.gender) == _normalize(profile.gender):
        return True, f"This scheme is open to {scheme.gender} applicants"
    return False, f"This scheme is only for {scheme.gender} applicants"


def _check_income(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if scheme.income_limit is None:
        return True, None
    if profile.annual_income is None:
        return True, None
    if profile.annual_income <= scheme.income_limit:
        income_str = f"₹{scheme.income_limit:,.0f}"
        return True, f"Your annual income is within the scheme limit of {income_str}"
    return False, f"Income limit for this scheme is ₹{scheme.income_limit:,.0f}"


def _check_occupation(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if not scheme.occupation:
        return True, None
    if profile.occupation is None:
        return True, None
    norm_occupations = [_normalize(o) for o in scheme.occupation]
    if _normalize(profile.occupation) in norm_occupations:
        return True, f"Your occupation ({profile.occupation}) matches the scheme's target group"
    return False, f"This scheme targets: {', '.join(scheme.occupation)}"


def _check_category(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if not scheme.category_requirement:
        return True, None
    if profile.category is None:
        return True, None
    norm_cats = [_normalize(c) for c in scheme.category_requirement]
    if _normalize(profile.category) in norm_cats:
        return True, f"Your social category ({profile.category}) is eligible"
    return False, f"This scheme is for: {', '.join(scheme.category_requirement)}"


def _check_state(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if not scheme.state:  # empty/null = all states
        return True, None
    if profile.state is None:
        return True, None
    norm_states = [_normalize(s) for s in scheme.state]
    if _normalize(profile.state) in norm_states:
        return True, f"This scheme is available in {profile.state}"
    return False, f"This scheme is only available in: {', '.join(scheme.state)}"


def _check_disability(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if scheme.disability_required is None:
        return True, None
    if scheme.disability_required is True:
        if profile.disability:
            return True, "This scheme is specifically for persons with disability"
        return False, "This scheme requires a disability certificate"
    return True, None


def _check_education(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if not scheme.education_requirement:
        return True, None
    if profile.education is None:
        return True, None
    norm_edus = [_normalize(e) for e in scheme.education_requirement]
    if _normalize(profile.education) in norm_edus:
        return True, f"Your education level ({profile.education}) meets the requirement"
    return False, f"Education requirement: {', '.join(scheme.education_requirement)}"


def _check_marital_status(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, Optional[str]]:
    if not scheme.marital_status_requirement:
        return True, None
    if profile.marital_status is None:
        return True, None
    norm_ms = [_normalize(m) for m in scheme.marital_status_requirement]
    if _normalize(profile.marital_status) in norm_ms:
        return True, None
    return False, f"This scheme requires: {', '.join(scheme.marital_status_requirement)}"


def compute_profile_completeness(profile: UserProfileInput) -> float:
    """Returns a 0-100 score indicating how complete the user's profile is."""
    fields = [
        profile.age, profile.gender, profile.state,
        profile.occupation, profile.annual_income, profile.category,
        profile.education, profile.marital_status,
    ]
    filled = sum(1 for f in fields if f is not None)
    return round((filled / len(fields)) * 100, 1)


def compute_match_score(reasons: List[str], checks_passed: int, total_checks: int) -> float:
    """Compute a 0-100 match score based on how many eligibility checks passed."""
    if total_checks == 0:
        return 50.0
    base_score = (checks_passed / total_checks) * 100
    # Small bonus for more matching reasons
    bonus = min(len(reasons) * 2, 10)
    return round(min(base_score + bonus, 100), 1)


def check_eligibility(scheme: Scheme, profile: UserProfileInput) -> Tuple[bool, List[str], float]:
    """
    Run all deterministic eligibility checks for a single scheme.

    Returns:
        (is_eligible, reasons, match_score)
    """
    checks = [
        _check_age(scheme, profile),
        _check_gender(scheme, profile),
        _check_income(scheme, profile),
        _check_occupation(scheme, profile),
        _check_category(scheme, profile),
        _check_state(scheme, profile),
        _check_disability(scheme, profile),
        _check_education(scheme, profile),
        _check_marital_status(scheme, profile),
    ]

    reasons = []
    disqualified = False
    checks_passed = 0

    for passed, reason in checks:
        if not passed:
            disqualified = True
        else:
            checks_passed += 1
            if reason:
                reasons.append(reason)

    if disqualified:
        return False, [], 0.0

    score = compute_match_score(reasons, checks_passed, len(checks))
    return True, reasons, score


def get_recommendations(
    schemes: List[Scheme],
    profile: UserProfileInput,
) -> List[RecommendationItem]:
    """
    Apply eligibility engine to all active schemes and return ranked results.
    """
    results = []

    for scheme in schemes:
        eligible, reasons, score = check_eligibility(scheme, profile)
        if eligible:
            results.append(
                RecommendationItem(
                    id=scheme.id,
                    name=scheme.name,
                    slug=scheme.slug,
                    category=scheme.category,
                    ministry=scheme.ministry,
                    description=scheme.description,
                    match_score=score,
                    reasons=reasons if reasons else ["This scheme may be relevant to your profile"],
                    benefits=scheme.benefits,
                    application_url=scheme.application_url,
                    documents=scheme.documents,
                )
            )

    # Sort by match score descending
    results.sort(key=lambda x: x.match_score, reverse=True)
    return results
