"""
JanMitra – AI Assistant and RAG Retrieval Tests
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.models import Scheme, User, Conversation, Message, MessageRole
from app.schemas.schemas import UserProfileInput, ChatRequest
from app.ai.retrieval import retrieve_relevant_schemes
from app.ai.assistant import get_ai_response, _detect_language, _generate_grounded_fallback


@pytest.fixture
def db_session():
    """In-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test schemes
    scheme1 = Scheme(
        id=1,
        name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        slug="pm-kisan",
        category="Agriculture",
        ministry="Ministry of Agriculture and Farmers Welfare",
        description="Income support of Rs. 6000 per year for farmer families.",
        benefits="Rs. 6000 per year in three 4-monthly installments of Rs. 2000.",
        documents=["Aadhaar Card", "Landholding papers", "Bank passbook"],
        occupation=["farmer", "agriculture"],
        application_url="https://pmkisan.gov.in",
        official_source_url="https://pmkisan.gov.in",
        active=True,
    )
    scheme2 = Scheme(
        id=2,
        name="Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)",
        slug="ayushman-bharat",
        category="Healthcare",
        ministry="Ministry of Health and Family Welfare",
        description="Health coverage up to Rs. 5 lakh per family per year.",
        benefits="Cashless treatment up to Rs. 5,00,000 per family per year.",
        documents=["Aadhaar Card", "Ration Card"],
        application_url="https://mera.pmjay.gov.in",
        official_source_url="https://nha.gov.in",
        active=True,
    )
    session.add(scheme1)
    session.add(scheme2)
    session.commit()

    yield session
    session.close()


def test_language_detection():
    assert _detect_language("Tell me about PM Kisan") == "en"
    assert _detect_language("प्रधानमंत्री किसान सम्मान निधि क्या है?") == "hi"
    assert _detect_language("पीएम किसान योजनेची माहिती काय आहे?") == "mr"
    assert _detect_language("kisan yojana kya hai") == "hi"
    assert _detect_language("yojana mahiti aahe ka") == "mr"


def test_retrieval_by_acronym(db_session):
    results = retrieve_relevant_schemes("pmkisan eligibility", db_session)
    assert len(results) > 0
    assert "PM-KISAN" in results[0]["name"]


def test_retrieval_by_occupation(db_session):
    profile = UserProfileInput(occupation="farmer")
    results = retrieve_relevant_schemes("what schemes can I get?", db_session, user_profile=profile)
    assert len(results) > 0
    assert any("Kisan" in r["name"] for r in results)


def test_grounded_fallback_english(db_session):
    schemes = retrieve_relevant_schemes("PM-KISAN", db_session)
    reply = _generate_grounded_fallback("Tell me about PM-KISAN", schemes)
    assert "PM-KISAN" in reply
    assert "Key Benefits" in reply or "Overview" in reply
    assert "Disclaimer" in reply or "disclaimer" in reply.lower()
    assert "https://pmkisan.gov.in" in reply


def test_grounded_fallback_hindi(db_session):
    schemes = retrieve_relevant_schemes("किसान योजना", db_session)
    reply = _generate_grounded_fallback("किसान योजना क्या है?", schemes)
    assert "विवरण" in reply or "लाभ" in reply
    assert "अस्वीकरण" in reply


def test_grounded_fallback_marathi(db_session):
    schemes = retrieve_relevant_schemes("किसान योजना", db_session)
    reply = _generate_grounded_fallback("पीएम किसान योजनेची माहिती द्या", schemes)
    assert "योजनेचे स्वरूप" in reply or "लाभ" in reply
    assert "अस्वीकरण" in reply


@pytest.mark.asyncio
async def test_ai_response_fallback_safety():
    # Calling without GEMINI_API_KEY set must return safe grounded response
    reply = await get_ai_response(
        message="Am I 100% guaranteed to get PM Kisan?",
        conversation_history=[],
        scheme_data=[{
            "name": "PM-KISAN",
            "category": "Agriculture",
            "description": "Income support",
            "benefits": "6000 INR",
            "documents": ["Aadhaar"],
            "application_url": "https://pmkisan.gov.in",
            "official_source_url": "https://pmkisan.gov.in",
        }]
    )
    assert "guaranteed" not in reply.lower() or "may be eligible" in reply.lower()
    assert "PM-KISAN" in reply

