"""
JanMitra – Endpoints and Integration Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import Scheme, User
from app.government.validator import validate_scheme_dict
from sqlalchemy.pool import StaticPool

# Test DB setup
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_test_data():
    """Populate test database before each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    scheme1 = Scheme(
        id=1,
        name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        slug="pm-kisan",
        category="Agriculture",
        ministry="Ministry of Agriculture",
        description="Farmer income support",
        benefits="Rs 6,000 annually",
        documents=["Aadhaar", "Land Records"],
        min_age=18,
        occupation=["farmer"],
        application_url="https://pmkisan.gov.in",
        official_source_url="https://pmkisan.gov.in",
        active=True,
    )
    scheme2 = Scheme(
        id=2,
        name="Ayushman Bharat (AB-PMJAY)",
        slug="ayushman-bharat",
        category="Healthcare",
        ministry="Ministry of Health",
        description="Health insurance coverage",
        benefits="Up to Rs 5 Lakh cashless cover",
        documents=["Aadhaar", "Ration Card"],
        application_url="https://mera.pmjay.gov.in",
        official_source_url="https://nha.gov.in",
        active=True,
    )
    user = User(
        id=1,
        age=30,
        gender="male",
        state="Maharashtra",
        occupation="farmer",
        annual_income=150000,
        category="OBC",
    )
    db.add(scheme1)
    db.add(scheme2)
    db.add(user)
    db.commit()
    db.close()


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "ai_available" in data


def test_schemes_list_and_search():
    # Listing
    res = client.get("/api/schemes")
    assert res.status_code == 200
    assert len(res.json()) >= 2

    # Search
    res_search = client.get("/api/schemes?q=kisan")
    assert res_search.status_code == 200
    schemes = res_search.json()
    assert len(schemes) == 1
    assert "Kisan" in schemes[0]["name"]

    # Category filter
    res_cat = client.get("/api/schemes?category=Healthcare")
    assert res_cat.status_code == 200
    assert len(res_cat.json()) == 1


def test_scheme_detail():
    res = client.get("/api/schemes/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["slug"] == "pm-kisan"


def test_recommendation_api():
    profile = {
        "age": 30,
        "gender": "male",
        "state": "Maharashtra",
        "occupation": "farmer",
        "annual_income": 150000,
        "category": "OBC",
    }
    res = client.post("/api/recommend", json=profile)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    assert data["profile_completeness"] > 0
    assert any(s["slug"] == "pm-kisan" for s in data["schemes"])


def test_saved_schemes_crud():
    # Save scheme
    res_save = client.post("/api/saved/1?user_id=1")
    assert res_save.status_code in (200, 201)

    # Get saved
    res_get = client.get("/api/saved?user_id=1")
    assert res_get.status_code == 200
    saved = res_get.json()
    assert len(saved) >= 1
    assert saved[0]["scheme_id"] == 1

    # Remove saved
    res_del = client.delete("/api/saved/1?user_id=1")
    assert res_del.status_code == 200

    # Verify removal
    res_get2 = client.get("/api/saved?user_id=1")
    assert len(res_get2.json()) == 0


def test_checklist_crud():
    # Get checklist (auto-populates from documents)
    res = client.get("/api/checklist/1?user_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert data["completed"] == 0

    first_item_id = data["items"][0]["id"]

    # Update item to completed
    res_upd = client.patch(f"/api/checklist/{first_item_id}?user_id=1", json={"completed": True})
    assert res_upd.status_code == 200
    assert res_upd.json()["completed"] is True

    # Recheck progress
    res_check = client.get("/api/checklist/1?user_id=1")
    assert res_check.json()["completed"] == 1
    assert res_check.json()["progress_percent"] > 0


def test_applications_crud():
    # Create application
    res = client.post("/api/applications?user_id=1", json={"scheme_id": 1, "status": "documents_pending"})
    assert res.status_code == 201
    app_id = res.json()["id"]

    # Get applications
    res_get = client.get("/api/applications?user_id=1")
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 1

    # Update status
    res_patch = client.patch(f"/api/applications/{app_id}?user_id=1", json={"status": "applied"})
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "applied"


def test_compare_schemes():
    res = client.post("/api/compare", json={"scheme_ids": [1, 2]})
    assert res.status_code == 200
    schemes = res.json()["schemes"]
    assert len(schemes) == 2


def test_assistant_chat_endpoint():
    req = {
        "user_id": 1,
        "message": "What is PM-KISAN?",
        "user_profile": {
            "occupation": "farmer"
        }
    }
    res = client.post("/api/assistant/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    assert "sources" in data
    assert "disclaimer" in data


def test_scheme_validation():
    # Valid record
    valid_data = {
        "name": "Pradhan Mantri Awas Yojana",
        "description": "Housing for all",
        "category": "Housing",
        "official_source_url": "pmaymis.gov.in"
    }
    is_valid, err, cleaned = validate_scheme_dict(valid_data)
    assert is_valid is True
    assert cleaned["official_source_url"] == "https://pmaymis.gov.in"
    assert cleaned["slug"] == "pradhan-mantri-awas-yojana"

    # Missing name
    is_valid, err, _ = validate_scheme_dict({"description": "Test", "category": "General"})
    assert is_valid is False
    assert "name" in err
