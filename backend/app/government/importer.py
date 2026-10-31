"""
JSON / CSV Data Importer

Imports and validates government scheme data from verified local JSON/CSV files.
Used for reliable offline import and when official APIs are unavailable or require keys.

All imported records are strictly validated before database insertion:
  - Required fields (name, category, description)
  - Official source URL & verification date
  - Non-destructive updates to existing records
"""
import json
import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.government.base import GovernmentDataProvider
from app.government.validator import validate_scheme_dict
from app.database import SessionLocal, engine, Base
from app.models.models import Scheme

logger = logging.getLogger(__name__)

# Search paths for schemes data
DATA_DIRS = [
    Path(__file__).parent.parent.parent.parent / "data" / "schemes",
    Path(__file__).parent.parent.parent / "data" / "schemes",
    Path("data/schemes"),
]


class SchemeImporter(GovernmentDataProvider):
    """Imports and synchronizes verified scheme data from JSON and CSV sources."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or self._find_data_dir()

    def _find_data_dir(self) -> Path:
        for d in DATA_DIRS:
            if d.exists():
                return d
        return DATA_DIRS[0]

    @property
    def source_name(self) -> str:
        return "Verified Scheme Datasets (JSON/CSV)"

    @property
    def source_url(self) -> str:
        return "https://www.myscheme.gov.in"

    async def verify_source(self) -> bool:
        return self.data_dir.exists() and (
            any(self.data_dir.glob("*.json")) or any(self.data_dir.glob("*.csv"))
        )

    def load_from_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load schemes from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "schemes" in data:
                    return data["schemes"]
                elif isinstance(data, dict):
                    return [data]
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
        return []

    def load_from_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load schemes from a CSV file."""
        schemes = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    schemes.append(dict(row))
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
        return schemes

    async def fetch_schemes(self) -> List[dict]:
        """Load all schemes from both JSON and CSV files in the data directory."""
        all_schemes = []
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return []

        for f in sorted(self.data_dir.glob("*")):
            if f.suffix.lower() == ".json":
                loaded = self.load_from_json(f)
                logger.info(f"Loaded {len(loaded)} records from {f.name}")
                all_schemes.extend(loaded)
            elif f.suffix.lower() == ".csv":
                loaded = self.load_from_csv(f)
                logger.info(f"Loaded {len(loaded)} records from {f.name}")
                all_schemes.extend(loaded)

        return all_schemes

    async def fetch_scheme_details(self, scheme_id: str) -> Optional[dict]:
        schemes = await self.fetch_schemes()
        for s in schemes:
            if str(s.get("id", "")) == str(scheme_id) or s.get("slug") == scheme_id:
                return s
        return None

    def sync_to_database(self) -> Tuple[int, int, int]:
        """
        Validate and sync verified schemes into the database.
        
        Returns:
            (inserted_count, updated_count, error_count)
        """
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

        import asyncio
        schemes_raw = asyncio.run(self.fetch_schemes())

        inserted = 0
        updated = 0
        errors = 0

        try:
            for raw in schemes_raw:
                is_valid, err, cleaned = validate_scheme_dict(raw)
                if not is_valid:
                    logger.warning(f"Skipping invalid scheme '{raw.get('name')}': {err}")
                    errors += 1
                    continue

                slug = cleaned["slug"]
                existing = db.query(Scheme).filter(Scheme.slug == slug).first()

                if existing:
                    # Non-destructive update: only overwrite if new value is non-empty
                    for k, v in cleaned.items():
                        if k in ("id", "created_at"):
                            continue
                        if v is not None:
                            setattr(existing, k, v)
                    updated += 1
                else:
                    new_scheme = Scheme(
                        name=cleaned["name"],
                        slug=cleaned["slug"],
                        category=cleaned["category"],
                        ministry=cleaned.get("ministry"),
                        department=cleaned.get("department"),
                        description=cleaned["description"],
                        detailed_description=cleaned.get("detailed_description"),
                        min_age=cleaned.get("min_age"),
                        max_age=cleaned.get("max_age"),
                        income_limit=cleaned.get("income_limit"),
                        gender=cleaned.get("gender"),
                        occupation=cleaned.get("occupation"),
                        category_requirement=cleaned.get("category_requirement"),
                        state=cleaned.get("state"),
                        education_requirement=cleaned.get("education_requirement"),
                        disability_required=cleaned.get("disability_required"),
                        marital_status_requirement=cleaned.get("marital_status_requirement"),
                        benefits=cleaned.get("benefits"),
                        documents=cleaned.get("documents"),
                        application_process=cleaned.get("application_process"),
                        application_url=cleaned.get("application_url"),
                        official_source_url=cleaned.get("official_source_url"),
                        source_name=cleaned.get("source_name", "Government of India"),
                        last_verified_at=cleaned.get("last_verified_at"),
                        active=cleaned.get("active", True),
                    )
                    db.add(new_scheme)
                    inserted += 1

            db.commit()
            logger.info(f"Sync complete: {inserted} added, {updated} updated, {errors} errors")
            return inserted, updated, errors

        except Exception as e:
            db.rollback()
            logger.error(f"Database sync failed: {e}")
            raise
        finally:
            db.close()


# Keep backward compatibility alias
JSONImporter = SchemeImporter


if __name__ == "__main__":
    importer = SchemeImporter()
    ins, upd, errs = importer.sync_to_database()
    print(f"✅ Imported {ins} new schemes, updated {upd} schemes, encountered {errs} errors.")
