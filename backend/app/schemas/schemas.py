"""
JanMitra – Pydantic Schemas (Request / Response models)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator, field_validator
from app.models.models import ApplicationStatus, MessageRole


# ─────────────────────────────────────────────
#  User schemas
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    email: Optional[str] = None
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    education: Optional[str] = None
    marital_status: Optional[str] = None
    disability: Optional[bool] = False
    disability_type: Optional[str] = None


class UserUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    education: Optional[str] = None
    marital_status: Optional[str] = None
    disability: Optional[bool] = None
    disability_type: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    state: Optional[str]
    district: Optional[str]
    occupation: Optional[str]
    annual_income: Optional[float]
    category: Optional[str]
    education: Optional[str]
    marital_status: Optional[str]
    disability: Optional[bool]
    disability_type: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Scheme schemas
# ─────────────────────────────────────────────

class SchemeBase(BaseModel):
    name: str
    slug: str
    category: str
    ministry: Optional[str] = None
    department: Optional[str] = None
    description: str
    detailed_description: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    income_limit: Optional[float] = None
    gender: Optional[str] = None
    occupation: Optional[List[str]] = None
    category_requirement: Optional[List[str]] = None
    state: Optional[List[str]] = None
    education_requirement: Optional[List[str]] = None
    disability_required: Optional[bool] = None
    marital_status_requirement: Optional[List[str]] = None
    benefits: Optional[str] = None
    documents: Optional[List[str]] = None
    application_process: Optional[str] = None
    application_url: Optional[str] = None
    official_source_url: Optional[str] = None
    source_name: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    active: bool = True


class SchemeCreate(SchemeBase):
    pass


class SchemeResponse(SchemeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchemeListResponse(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    ministry: Optional[str]
    description: str
    benefits: Optional[str]
    application_url: Optional[str]
    gender: Optional[str]
    min_age: Optional[int]
    max_age: Optional[int]
    income_limit: Optional[float]
    state: Optional[List[str]]
    active: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Recommendation schemas
# ─────────────────────────────────────────────

class UserProfileInput(BaseModel):
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    education: Optional[str] = None
    marital_status: Optional[str] = None
    disability: Optional[bool] = False


class RecommendationItem(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    ministry: Optional[str]
    description: str
    match_score: float
    reasons: List[str]
    benefits: Optional[str]
    application_url: Optional[str]
    documents: Optional[List[str]]


class RecommendationResponse(BaseModel):
    count: int
    profile_completeness: float
    disclaimer: str = (
        "Based on the information you provided, you may be eligible for these schemes. "
        "Final eligibility should be confirmed with the official scheme authority."
    )
    schemes: List[RecommendationItem]


# ─────────────────────────────────────────────
#  Saved Schemes
# ─────────────────────────────────────────────

class SavedSchemeResponse(BaseModel):
    id: int
    user_id: int
    scheme_id: int
    created_at: datetime
    scheme: SchemeListResponse

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Application
# ─────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    scheme_id: int
    status: ApplicationStatus = ApplicationStatus.interested
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    scheme_id: int
    status: ApplicationStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    scheme: Optional[SchemeListResponse] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Checklist
# ─────────────────────────────────────────────

class ChecklistItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 0


class ChecklistItemUpdate(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None


class ChecklistItemResponse(BaseModel):
    id: int
    scheme_id: int
    user_id: int
    title: str
    description: Optional[str]
    completed: bool
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChecklistResponse(BaseModel):
    scheme_id: int
    total: int
    completed: int
    progress_percent: float
    items: List[ChecklistItemResponse]


# ─────────────────────────────────────────────
#  Conversation / AI
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    message: str
    user_profile: Optional[UserProfileInput] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    sources: List[str] = []
    disclaimer: str = (
        "This response is for informational purposes only. "
        "Always verify information on official government portals."
    )


# ─────────────────────────────────────────────
#  Comparison
# ─────────────────────────────────────────────

class CompareRequest(BaseModel):
    scheme_ids: List[int] = Field(..., min_length=2, max_length=3)


class CompareResponse(BaseModel):
    schemes: List[SchemeResponse]


# ─────────────────────────────────────────────
#  Generic
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    ai_available: bool
    version: str = "1.0.0"
