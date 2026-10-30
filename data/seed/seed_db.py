"""
JanMitra – Database Seed Script

Seeds the database with verified government scheme data from data/schemes/schemes.json

Usage:
    cd backend
    python -m data.seed.seed_db
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.database import SessionLocal, engine, Base
from app.models.models import Scheme


def slugify(text: str) -> str:
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text[:200]


def load_schemes(data_dir: Path) -> list:
    schemes_file = data_dir / "schemes" / "schemes.json"
    if not schemes_file.exists():
        print(f"ERROR: {schemes_file} not found")
        return []

    with open(schemes_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "schemes" in data:
        return data["schemes"]
    return []


def seed_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    data_dir = Path(__file__).parent.parent.parent / "data"
    schemes_data = load_schemes(data_dir)

    if not schemes_data:
        print("No schemes found to seed")
        return

    db = SessionLocal()
    try:
        seeded = 0
        skipped = 0

        for scheme_dict in schemes_data:
            # Check if already exists
            slug = scheme_dict.get("slug") or slugify(scheme_dict.get("name", ""))
            existing = db.query(Scheme).filter(Scheme.slug == slug).first()

            if existing:
                skipped += 1
                continue

            # Parse dates
            last_verified = None
            if scheme_dict.get("last_verified_at"):
                try:
                    last_verified = datetime.strptime(
                        scheme_dict["last_verified_at"], "%Y-%m-%d"
                    )
                except Exception:
                    pass

            scheme = Scheme(
                name=scheme_dict["name"],
                slug=slug,
                category=scheme_dict.get("category", "General"),
                ministry=scheme_dict.get("ministry"),
                department=scheme_dict.get("department"),
                description=scheme_dict["description"],
                detailed_description=scheme_dict.get("detailed_description"),
                min_age=scheme_dict.get("min_age"),
                max_age=scheme_dict.get("max_age"),
                income_limit=scheme_dict.get("income_limit"),
                gender=scheme_dict.get("gender"),
                occupation=scheme_dict.get("occupation"),
                category_requirement=scheme_dict.get("category_requirement"),
                state=scheme_dict.get("state"),
                education_requirement=scheme_dict.get("education_requirement"),
                disability_required=scheme_dict.get("disability_required"),
                marital_status_requirement=scheme_dict.get("marital_status_requirement"),
                benefits=scheme_dict.get("benefits"),
                documents=scheme_dict.get("documents"),
                application_process=scheme_dict.get("application_process"),
                application_url=scheme_dict.get("application_url"),
                official_source_url=scheme_dict.get("official_source_url"),
                source_name=scheme_dict.get("source_name"),
                last_verified_at=last_verified,
                active=scheme_dict.get("active", True),
            )
            db.add(scheme)
            seeded += 1

        db.commit()
        print(f"✅ Seeded {seeded} schemes | ⏭️  Skipped {skipped} (already exist)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
