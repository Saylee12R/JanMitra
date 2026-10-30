"""
JanMitra – SQLAlchemy ORM Models
"""
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ─────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────

class ApplicationStatus(str, enum.Enum):
    interested = "interested"
    documents_pending = "documents_pending"
    ready_to_apply = "ready_to_apply"
    applied = "applied"
    completed = "completed"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ─────────────────────────────────────────────
#  User
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Auth (optional – guest users have no email/password)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    # Profile
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    occupation = Column(String(100), nullable=True)
    annual_income = Column(Float, nullable=True)
    category = Column(String(50), nullable=True)  # General/OBC/SC/ST/EWS
    education = Column(String(100), nullable=True)
    marital_status = Column(String(50), nullable=True)
    disability = Column(Boolean, nullable=True, default=False)
    disability_type = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    saved_schemes = relationship("SavedScheme", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
#  Scheme
# ─────────────────────────────────────────────

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False)
    ministry = Column(String(300), nullable=True)
    department = Column(String(300), nullable=True)
    description = Column(Text, nullable=False)
    detailed_description = Column(Text, nullable=True)

    # Eligibility fields (for deterministic matching)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    income_limit = Column(Float, nullable=True)
    gender = Column(String(20), nullable=True)   # "male" | "female" | "any"
    # JSON arrays stored as strings / JSON columns
    occupation = Column(JSON, nullable=True)     # list[str]
    category_requirement = Column(JSON, nullable=True)  # list[str]
    state = Column(JSON, nullable=True)          # list[str] | null = all states
    education_requirement = Column(JSON, nullable=True)  # list[str]
    disability_required = Column(Boolean, nullable=True)  # None = not required
    marital_status_requirement = Column(JSON, nullable=True)

    # Scheme information
    benefits = Column(Text, nullable=True)
    documents = Column(JSON, nullable=True)         # list[str]
    application_process = Column(Text, nullable=True)
    application_url = Column(String(1000), nullable=True)
    official_source_url = Column(String(1000), nullable=True)
    source_name = Column(String(300), nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    eligibility_rules = relationship("EligibilityRule", back_populates="scheme", cascade="all, delete-orphan")
    saved_by = relationship("SavedScheme", back_populates="scheme")
    applications = relationship("Application", back_populates="scheme")
    checklist_items = relationship("ChecklistItem", back_populates="scheme")


# ─────────────────────────────────────────────
#  Eligibility Rules
# ─────────────────────────────────────────────

class EligibilityRule(Base):
    """Structured eligibility rules – evaluated deterministically."""
    __tablename__ = "eligibility_rules"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    rule_type = Column(String(50), nullable=False)  # age|income|gender|...
    operator = Column(String(20), nullable=False)   # eq|gte|lte|in|not_in
    value = Column(JSON, nullable=False)
    description = Column(String(500), nullable=True)

    scheme = relationship("Scheme", back_populates="eligibility_rules")


# ─────────────────────────────────────────────
#  Saved Schemes
# ─────────────────────────────────────────────

class SavedScheme(Base):
    __tablename__ = "saved_schemes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_schemes")
    scheme = relationship("Scheme", back_populates="saved_by")


# ─────────────────────────────────────────────
#  Applications
# ─────────────────────────────────────────────

class Application(Base):
    """
    Tracks user's self-reported application progress.
    NOTE: 'applied' or 'completed' status is NOT verified by any government
    authority. It reflects only what the user has self-reported.
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    status = Column(
        SAEnum(ApplicationStatus),
        default=ApplicationStatus.interested,
        nullable=False
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    scheme = relationship("Scheme", back_populates="applications")


# ─────────────────────────────────────────────
#  Checklist
# ─────────────────────────────────────────────

class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="checklist_items")
    user = relationship("User", back_populates="checklist_items")


# ─────────────────────────────────────────────
#  Conversations / Messages
# ─────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
