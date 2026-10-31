"""
JanMitra – AI Assistant, Intent Detection & RAG Retrieval Tests
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.models import Scheme, User, Conversation, Message, MessageRole
from app.schemas.schemas import UserProfileInput, ChatRequest
from app.ai.retrieval import retrieve_relevant_schemes
from app.ai.assistant import (
    get_ai_response,
    _detect_language,
    _generate_grounded_fallback,
    _build_scheme_context,
    _build_profile_context,
)
from app.ai.intent import (
    detect_intent,
    is_ambiguous_query,
    format_intent_response,
    INTENT_BENEFITS,
    INTENT_DOCUMENTS,
    INTENT_ELIGIBILITY,
    INTENT_APPLICATION,
    INTENT_DEADLINE,
    INTENT_AGE_INCOME,
    INTENT_STATUS,
    INTENT_OFFICIAL_LINK,
    INTENT_COMPARISON,
    INTENT_GENERAL,
)


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
        min_age=18,
        max_age=100,
        occupation=["farmer", "agriculture"],
        application_process="Farmers can register online at pmkisan.gov.in or visit the nearest CSC / State Agriculture Nodal Office.",
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
        benefits="Cashless treatment up to Rs. 5,00,000 per family per year at empaneled hospitals.",
        documents=["Aadhaar Card", "Ration Card"],
        application_process="Check eligibility at mera.pmjay.gov.in and generate Golden Card at nearest Ayushman Mitra desk.",
        application_url="https://mera.pmjay.gov.in",
        official_source_url="https://nha.gov.in",
        active=True,
    )
    scheme3 = Scheme(
        id=3,
        name="Post-Matric Scholarship for SC Students",
        slug="post-matric-sc",
        category="Education",
        ministry="Ministry of Social Justice and Empowerment",
        description="Financial assistance for SC students pursuing post-matric studies.",
        benefits="Full tuition fee reimbursement and monthly maintenance allowance.",
        documents=["Caste Certificate", "Income Certificate", "Marksheet"],
        application_url="https://scholarships.gov.in",
        official_source_url="https://socialjustice.gov.in",
        active=True,
    )
    scheme4 = Scheme(
        id=4,
        name="National Means-cum-Merit Scholarship",
        slug="nmms-scholarship",
        category="Education",
        ministry="Ministry of Education",
        description="Scholarship for meritorious students from economically weaker sections.",
        benefits="Rs. 12,000 per annum (Rs. 1000 per month).",
        documents=["Income Certificate", "School Enrollment Proof"],
        application_url="https://scholarships.gov.in",
        official_source_url="https://education.gov.in",
        active=True,
    )
    session.add_all([scheme1, scheme2, scheme3, scheme4])
    session.commit()

    yield session
    session.close()


# ── Language Detection Tests ───────────────────────────────────────────────

def test_language_detection():
    assert _detect_language("Tell me about PM Kisan") == "en"
    assert _detect_language("प्रधानमंत्री किसान सम्मान निधि क्या है?") == "hi"
    assert _detect_language("पीएम किसान योजनेची माहिती काय आहे?") == "mr"
    assert _detect_language("kisan yojana kya hai") == "hi"
    assert _detect_language("PM Kisan mein kitne paise milte hain?") == "hi"
    assert _detect_language("या योजनेचे फायदे काय आहेत?") == "mr"
    assert _detect_language("yojaneche fayde kay aahe") == "mr"


# ── Multilingual Intent Detection Tests ────────────────────────────────────

def test_intent_detection_benefits():
    assert detect_intent("PM Kisan mein kitne paise milte hain?") == INTENT_BENEFITS
    assert detect_intent("What are the financial benefits of PM-KISAN?") == INTENT_BENEFITS
    assert detect_intent("या योजनेचे फायदे काय आहेत?") == INTENT_BENEFITS
    assert detect_intent("kiti rakkam milnar?") == INTENT_BENEFITS
    assert detect_intent("कितने रुपये मिलेंगे?") == INTENT_BENEFITS


def test_intent_detection_documents():
    assert detect_intent("Is scheme ke documents kya hai?") == INTENT_DOCUMENTS
    assert detect_intent("What documents are required to apply?") == INTENT_DOCUMENTS
    assert detect_intent("कागदपत्रे कोणती लागतील?") == INTENT_DOCUMENTS
    assert detect_intent("dastavej kya lagenge?") == INTENT_DOCUMENTS
    assert detect_intent("काय कागदपत्रे लागतील?") == INTENT_DOCUMENTS


def test_intent_detection_eligibility():
    assert detect_intent("Mere liye eligible hai kya?") == INTENT_ELIGIBILITY
    assert detect_intent("Am I eligible for this scheme?") == INTENT_ELIGIBILITY
    assert detect_intent("Who can apply for Ayushman Bharat?") == INTENT_ELIGIBILITY
    assert detect_intent("पात्रता काय आहे?") == INTENT_ELIGIBILITY
    assert detect_intent("is scheme ke liye kaun patra hai?") == INTENT_ELIGIBILITY


def test_intent_detection_application():
    assert detect_intent("Apply kaise karna hai?") == INTENT_APPLICATION
    assert detect_intent("How to apply for PM Kisan online?") == INTENT_APPLICATION
    assert detect_intent("अर्ज कसा करावा?") == INTENT_APPLICATION
    assert detect_intent("aavedan kaise kare?") == INTENT_APPLICATION
    assert detect_intent("kasa arja karaycha?") == INTENT_APPLICATION


def test_intent_detection_deadline():
    assert detect_intent("Iski last date kya hai?") == INTENT_DEADLINE
    assert detect_intent("What is the application deadline?") == INTENT_DEADLINE
    assert detect_intent("शेवटची तारीख काय आहे?") == INTENT_DEADLINE
    assert detect_intent("aakhri tarikh kab tak hai?") == INTENT_DEADLINE
    assert detect_intent("अंतिम तारीख काय?") == INTENT_DEADLINE


def test_intent_detection_age_income():
    assert detect_intent("What is the age limit for this scheme?") == INTENT_AGE_INCOME
    assert detect_intent("Annual income limit kitni hai?") == INTENT_AGE_INCOME
    assert detect_intent("वय मर्यादा काय आहे?") == INTENT_AGE_INCOME
    assert detect_intent("उम्र सीमा क्या है?") == INTENT_AGE_INCOME


def test_intent_detection_comparison():
    assert detect_intent("Compare PM Kisan and Ayushman Bharat") == INTENT_COMPARISON
    assert detect_intent("dono schemes mein kya antar hai?") == INTENT_COMPARISON
    assert detect_intent("या दोन्ही योजनांमध्ये काय फरक आहे?") == INTENT_COMPARISON


# ── Same Scheme, Different Questions, Different Targeted Answers ────────────

def test_same_scheme_different_answers(db_session):
    schemes = retrieve_relevant_schemes("PM-KISAN", db_session)
    assert len(schemes) > 0

    # Question 1: Benefits question
    ans_benefits = _generate_grounded_fallback("PM Kisan mein kitne paise milte hain?", schemes)
    assert "लाभ" in ans_benefits or "Benefits" in ans_benefits
    assert "6000" in ans_benefits or "6,000" in ans_benefits
    # Must NOT dump documents or application steps
    assert "Landholding papers" not in ans_benefits
    assert "CSC" not in ans_benefits

    # Question 2: Documents question
    ans_docs = _generate_grounded_fallback("Is scheme ke documents kya hai?", schemes)
    assert "दस्तावेज़" in ans_docs or "Documents" in ans_docs
    assert "Aadhaar Card" in ans_docs
    assert "Landholding papers" in ans_docs
    # Must NOT dump benefits or monetary amounts
    assert "Rs. 6000" not in ans_docs

    # Question 3: Application question
    ans_apply = _generate_grounded_fallback("Apply kaise karna hai?", schemes)
    assert "आवेदन" in ans_apply or "Apply" in ans_apply or "Steps" in ans_apply
    assert "pmkisan.gov.in" in ans_apply
    # Must NOT dump document checklist
    assert "Landholding papers" not in ans_apply

    # Question 4: Deadline question
    ans_deadline = _generate_grounded_fallback("Iski last date kya hai?", schemes)
    assert "अंतिम तिथि" in ans_deadline or "deadline" in ans_deadline.lower() or "तारीख" in ans_deadline
    assert "कोई निश्चित अंतिम तिथि" in ans_deadline or "no fixed closing date" in ans_deadline.lower() or "निरंतर" in ans_deadline
    # Must NOT invent a fake date
    assert "31st March" not in ans_deadline
    assert "31 December" not in ans_deadline

    # Question 5: Marathi benefits question
    ans_mr_benefits = _generate_grounded_fallback("या योजनेचे फायदे काय आहेत?", schemes)
    assert "मिळणारे लाभ" in ans_mr_benefits or "फायदे" in ans_mr_benefits
    assert "6000" in ans_mr_benefits or "6,000" in ans_mr_benefits
    assert "अस्वीकरण" in ans_mr_benefits


# ── Eligibility with User Profile ──────────────────────────────────────────

def test_eligibility_grounded_with_profile(db_session):
    schemes = retrieve_relevant_schemes("PM-KISAN", db_session)
    profile = UserProfileInput(age=35, occupation="farmer", annual_income=120000, state="Maharashtra")
    
    reply = _generate_grounded_fallback("Mere liye eligible hai kya?", schemes, user_profile=profile)
    assert "पात्र" in reply or "Eligib" in reply
    assert "35" in reply or "farmer" in reply.lower() or "Farmer" in reply
    # Must never guarantee
    assert "guaranteed" not in reply.lower()


# ── Ambiguity Handling ─────────────────────────────────────────────────────

def test_ambiguity_handling(db_session):
    # Query matching multiple education/scholarship schemes broadly
    schemes = retrieve_relevant_schemes("scholarships for students", db_session)
    assert len(schemes) >= 2
    
    # Must detect ambiguity when asking broadly
    assert is_ambiguous_query("Which scholarships are available?", schemes) is True
    
    reply = _generate_grounded_fallback("Which scholarships are available?", schemes)
    assert "Post-Matric" in reply
    assert "National Means-cum-Merit" in reply
    assert "Which specific scheme would you like to" in reply or "कोणत्या विशिष्ट योजनेबद्दल" in reply or "किस विशिष्ट योजना" in reply


# ── Conversational Pronoun Context ─────────────────────────────────────────

def test_retrieval_with_pronoun_context(db_session):
    # If the user asks a follow-up without scheme name: "Is scheme ke documents kya hai?"
    history = [
        {"role": "user", "content": "Tell me about PM-KISAN"},
        {"role": "assistant", "content": "PM-KISAN is an income support scheme for farmers."}
    ]
    results = retrieve_relevant_schemes(
        "Is scheme ke documents kya hai?",
        db_session,
        conversation_history=history,
    )
    assert len(results) > 0
    assert "PM-KISAN" in results[0]["name"]


def test_conversation_followup_scheme_pinning(db_session):
    """Test that PM-KISAN remains the pinned active scheme across follow-ups."""
    # Turn 1: PM Kisan benefits
    t1_results = retrieve_relevant_schemes("PM Kisan mein kitne paise milte hain?", db_session)
    assert len(t1_results) == 1
    assert "PM-KISAN" in t1_results[0]["name"]

    history = [
        {"role": "user", "content": "PM Kisan mein kitne paise milte hain?"},
        {"role": "assistant", "content": "PM-KISAN provides Rs. 6000 per year."}
    ]

    # Turn 2: Documents follow-up
    t2_results = retrieve_relevant_schemes("Is scheme ke documents kya hai?", db_session, conversation_history=history)
    assert len(t2_results) == 1
    assert "PM-KISAN" in t2_results[0]["name"]

    history.extend([
        {"role": "user", "content": "Is scheme ke documents kya hai?"},
        {"role": "assistant", "content": "Aadhaar card, landholding papers, bank passbook."}
    ])

    # Turn 3: "Meri eligibility check karo" should stay on PM-KISAN (not switch to NMMS)
    t3_results = retrieve_relevant_schemes("Meri eligibility check karo.", db_session, conversation_history=history)
    assert len(t3_results) == 1
    assert "PM-KISAN" in t3_results[0]["name"]

    history.extend([
        {"role": "user", "content": "Meri eligibility check karo."},
        {"role": "assistant", "content": "PM-KISAN eligibility criteria."}
    ])

    # Turn 4: "iski last date kya hai?" should stay on PM-KISAN (not switch to scholarship)
    t4_results = retrieve_relevant_schemes("iski last date kya hai?", db_session, conversation_history=history)
    assert len(t4_results) == 1
    assert "PM-KISAN" in t4_results[0]["name"]

    # Turn 5: Explicitly naming Ayushman Bharat must change the active scheme
    t5_results = retrieve_relevant_schemes("Ayushman Bharat ke baare mein batao", db_session, conversation_history=history)
    assert len(t5_results) >= 1
    assert "Ayushman" in t5_results[0]["name"]


# ── Safety and Fallback Tests ──────────────────────────────────────────────

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


def test_none_type_formatting_safety():
    """Ensure None values for income_limit and annual_income do not cause NoneType formatting errors."""
    scheme_none_income = {
        "name": "PM-KISAN",
        "category": "Agriculture",
        "income_limit": None,
        "min_age": None,
        "max_age": None,
    }
    # Must not raise TypeError: unsupported format string passed to NoneType.__format__
    context = _build_scheme_context([scheme_none_income])
    assert "Income Limit: Not specified" in context

    # Test with valid integer
    scheme_int_income = {
        "name": "EWS Scheme",
        "income_limit": 300000,
    }
    context_int = _build_scheme_context([scheme_int_income])
    assert "₹300,000 annually" in context_int

    # Profile with None annual income
    profile_none = UserProfileInput(age=25, annual_income=None)
    profile_ctx_none = _build_profile_context(profile_none)
    assert "Age: 25 years" in profile_ctx_none
    assert "Annual Income" not in profile_ctx_none

    # Profile with valid annual income
    profile_val = UserProfileInput(age=25, annual_income=150000)
    profile_ctx_val = _build_profile_context(profile_val)
    assert "Annual Income: ₹150,000" in profile_ctx_val
