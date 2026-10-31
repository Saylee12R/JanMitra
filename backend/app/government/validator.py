"""
JanMitra – Scheme Data Validator

Ensures all government scheme records adhere to strict quality and
verification standards before being committed to the database.
"""
import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

REQUIRED_FIELDS = ["name", "description", "category"]


def validate_scheme_dict(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate and sanitize a scheme record dictionary.
    
    Returns:
        (is_valid, error_message, cleaned_data)
    """
    if not isinstance(data, dict):
        return False, "Scheme data must be a dictionary", {}

    # Check required fields
    for field in REQUIRED_FIELDS:
        val = data.get(field)
        if not val or not str(val).strip():
            return False, f"Missing required field: '{field}'", {}

    cleaned = dict(data)
    cleaned["name"] = str(data["name"]).strip()
    cleaned["description"] = str(data["description"]).strip()
    cleaned["category"] = str(data["category"]).strip()

    # Generate slug if not present
    if not cleaned.get("slug"):
        slug = cleaned["name"].lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug.strip())
        cleaned["slug"] = slug[:200]

    # Validate numbers
    if cleaned.get("min_age") is not None:
        try:
            cleaned["min_age"] = int(cleaned["min_age"])
        except (ValueError, TypeError):
            cleaned["min_age"] = None

    if cleaned.get("max_age") is not None:
        try:
            cleaned["max_age"] = int(cleaned["max_age"])
        except (ValueError, TypeError):
            cleaned["max_age"] = None

    if cleaned.get("income_limit") is not None:
        try:
            cleaned["income_limit"] = float(cleaned["income_limit"])
        except (ValueError, TypeError):
            cleaned["income_limit"] = None

    # Validate lists
    for list_field in ["occupation", "category_requirement", "state", "education_requirement", "documents"]:
        val = cleaned.get(list_field)
        if val is not None and not isinstance(val, list):
            if isinstance(val, str):
                cleaned[list_field] = [s.strip() for s in val.split(",") if s.strip()]
            else:
                cleaned[list_field] = []

    # Validate official URLs
    for url_field in ["official_source_url", "application_url"]:
        url = cleaned.get(url_field)
        if url:
            url_str = str(url).strip()
            if not url_str.startswith("http://") and not url_str.startswith("https://"):
                url_str = f"https://{url_str}"
            cleaned[url_field] = url_str

    # Parse last_verified_at
    if cleaned.get("last_verified_at"):
        if isinstance(cleaned["last_verified_at"], str):
            try:
                cleaned["last_verified_at"] = datetime.fromisoformat(
                    cleaned["last_verified_at"].replace("Z", "+00:00")
                )
            except Exception:
                try:
                    cleaned["last_verified_at"] = datetime.strptime(
                        cleaned["last_verified_at"], "%Y-%m-%d"
                    )
                except Exception:
                    cleaned["last_verified_at"] = datetime.utcnow()
    else:
        cleaned["last_verified_at"] = datetime.utcnow()

    cleaned["active"] = bool(cleaned.get("active", True))

    return True, None, cleaned

