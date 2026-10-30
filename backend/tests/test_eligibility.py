"""
JanMitra – Eligibility Engine Tests

Tests the deterministic eligibility engine with various user profiles.
"""
import pytest
from app.services.eligibility import check_eligibility, get_recommendations, compute_profile_completeness
from app.schemas.schemas import UserProfileInput


# ── Mock Scheme Helper ─────────────────────────────────────────────────────

class MockScheme:
    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "Test Scheme",
            "slug": "test-scheme",
            "category": "Test",
            "ministry": "Test Ministry",
            "description": "Test description",
            "min_age": None,
            "max_age": None,
            "income_limit": None,
            "gender": None,
            "occupation": None,
            "category_requirement": None,
            "state": None,
            "education_requirement": None,
            "disability_required": None,
            "marital_status_requirement": None,
            "benefits": "Test benefits",
            "documents": [],
            "application_url": None,
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


# ── Age Tests ──────────────────────────────────────────────────────────────

class TestAgeMatching:
    def test_within_age_range(self):
        scheme = MockScheme(min_age=18, max_age=35)
        profile = UserProfileInput(age=25)
        eligible, reasons, score = check_eligibility(scheme, profile)
        assert eligible is True
        assert score > 0

    def test_below_min_age(self):
        scheme = MockScheme(min_age=18)
        profile = UserProfileInput(age=16)
        eligible, _, score = check_eligibility(scheme, profile)
        assert eligible is False
        assert score == 0.0

    def test_above_max_age(self):
        scheme = MockScheme(max_age=40)
        profile = UserProfileInput(age=50)
        eligible, _, score = check_eligibility(scheme, profile)
        assert eligible is False

    def test_at_min_age_boundary(self):
        scheme = MockScheme(min_age=18)
        profile = UserProfileInput(age=18)
        eligible, _, score = check_eligibility(scheme, profile)
        assert eligible is True

    def test_at_max_age_boundary(self):
        scheme = MockScheme(max_age=40)
        profile = UserProfileInput(age=40)
        eligible, _, score = check_eligibility(scheme, profile)
        assert eligible is True

    def test_no_age_in_profile(self):
        """No age provided – should not disqualify."""
        scheme = MockScheme(min_age=18, max_age=35)
        profile = UserProfileInput()
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_no_age_requirement(self):
        scheme = MockScheme()
        profile = UserProfileInput(age=50)
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── Gender Tests ───────────────────────────────────────────────────────────

class TestGenderMatching:
    def test_female_scheme_female_user(self):
        scheme = MockScheme(gender="female")
        profile = UserProfileInput(gender="female")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_female_scheme_male_user(self):
        scheme = MockScheme(gender="female")
        profile = UserProfileInput(gender="male")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_any_gender_scheme(self):
        scheme = MockScheme(gender="any")
        profile = UserProfileInput(gender="male")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_no_gender_in_scheme(self):
        scheme = MockScheme(gender=None)
        profile = UserProfileInput(gender="female")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── Income Tests ────────────────────────────────────────────────────────────

class TestIncomeMatching:
    def test_within_income_limit(self):
        scheme = MockScheme(income_limit=250000)
        profile = UserProfileInput(annual_income=200000)
        eligible, reasons, _ = check_eligibility(scheme, profile)
        assert eligible is True
        assert any("income" in r.lower() for r in reasons)

    def test_above_income_limit(self):
        scheme = MockScheme(income_limit=250000)
        profile = UserProfileInput(annual_income=500000)
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_exactly_at_income_limit(self):
        scheme = MockScheme(income_limit=250000)
        profile = UserProfileInput(annual_income=250000)
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_no_income_limit(self):
        scheme = MockScheme(income_limit=None)
        profile = UserProfileInput(annual_income=1000000)
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_no_income_in_profile(self):
        """No income provided – should not disqualify."""
        scheme = MockScheme(income_limit=250000)
        profile = UserProfileInput()
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── Occupation Tests ────────────────────────────────────────────────────────

class TestOccupationMatching:
    def test_matching_occupation(self):
        scheme = MockScheme(occupation=["farmer", "agriculture"])
        profile = UserProfileInput(occupation="farmer")
        eligible, reasons, _ = check_eligibility(scheme, profile)
        assert eligible is True
        assert any("occupation" in r.lower() for r in reasons)

    def test_non_matching_occupation(self):
        scheme = MockScheme(occupation=["farmer"])
        profile = UserProfileInput(occupation="student")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_no_occupation_requirement(self):
        scheme = MockScheme(occupation=None)
        profile = UserProfileInput(occupation="student")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── Category Tests ──────────────────────────────────────────────────────────

class TestCategoryMatching:
    def test_matching_category(self):
        scheme = MockScheme(category_requirement=["SC", "ST"])
        profile = UserProfileInput(category="SC")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_non_matching_category(self):
        scheme = MockScheme(category_requirement=["SC"])
        profile = UserProfileInput(category="General")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_no_category_requirement(self):
        scheme = MockScheme(category_requirement=None)
        profile = UserProfileInput(category="OBC")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── State Tests ─────────────────────────────────────────────────────────────

class TestStateMatching:
    def test_matching_state(self):
        scheme = MockScheme(state=["Maharashtra", "Gujarat"])
        profile = UserProfileInput(state="Maharashtra")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True

    def test_non_matching_state(self):
        scheme = MockScheme(state=["Maharashtra"])
        profile = UserProfileInput(state="Bihar")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_all_states(self):
        """Empty state list means available in all states."""
        scheme = MockScheme(state=None)
        profile = UserProfileInput(state="Bihar")
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── Disability Tests ────────────────────────────────────────────────────────

class TestDisabilityMatching:
    def test_disability_required_user_has_disability(self):
        scheme = MockScheme(disability_required=True)
        profile = UserProfileInput(disability=True)
        eligible, reasons, _ = check_eligibility(scheme, profile)
        assert eligible is True
        assert any("disability" in r.lower() for r in reasons)

    def test_disability_required_user_no_disability(self):
        scheme = MockScheme(disability_required=True)
        profile = UserProfileInput(disability=False)
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_disability_not_required(self):
        """Scheme doesn't require disability – open to all."""
        scheme = MockScheme(disability_required=None)
        profile = UserProfileInput(disability=False)
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is True


# ── Multiple Conditions Tests ────────────────────────────────────────────────

class TestMultipleConditions:
    def test_all_conditions_match(self):
        scheme = MockScheme(
            min_age=18,
            max_age=35,
            gender="female",
            income_limit=300000,
            occupation=["student"],
            category_requirement=["SC", "OBC"],
            state=["Maharashtra"],
        )
        profile = UserProfileInput(
            age=22,
            gender="female",
            annual_income=200000,
            occupation="student",
            category="OBC",
            state="Maharashtra",
        )
        eligible, reasons, score = check_eligibility(scheme, profile)
        assert eligible is True
        assert score > 70
        assert len(reasons) >= 3

    def test_one_condition_fails(self):
        scheme = MockScheme(
            min_age=18,
            max_age=35,
            gender="female",
        )
        profile = UserProfileInput(
            age=40,  # Fails max_age
            gender="female",
        )
        eligible, _, _ = check_eligibility(scheme, profile)
        assert eligible is False

    def test_no_scheme_matches_profile(self):
        """Highly specific profile that shouldn't match any broad scheme."""
        schemes = [
            MockScheme(id=1, gender="male", occupation=["farmer"]),
            MockScheme(id=2, gender="female", min_age=60),
        ]
        profile = UserProfileInput(
            age=25,
            gender="female",
            occupation="student",
        )
        results = get_recommendations(schemes, profile)
        # Female student aged 25 shouldn't match male+farmer or female+60+
        assert all(r.id != 1 for r in results)


# ── Profile Completeness Tests ───────────────────────────────────────────────

class TestProfileCompleteness:
    def test_empty_profile(self):
        profile = UserProfileInput()
        score = compute_profile_completeness(profile)
        assert score == 0.0

    def test_full_profile(self):
        profile = UserProfileInput(
            age=25,
            gender="female",
            state="Maharashtra",
            occupation="student",
            annual_income=150000,
            category="General",
            education="undergraduate",
            marital_status="single",
        )
        score = compute_profile_completeness(profile)
        assert score == 100.0

    def test_partial_profile(self):
        profile = UserProfileInput(age=25, gender="female")
        score = compute_profile_completeness(profile)
        assert 0 < score < 100.0
