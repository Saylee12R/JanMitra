"""
JSON / CSV Data Importer

Imports government scheme data from verified local JSON/CSV files.
Used when official APIs are unavailable or require registration.

All data files in data/schemes/ must:
  - Contain only verified government scheme information
  - Include the official source URL
  - Include a last_verified_at date
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.government.base import GovernmentDataProvider

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "schemes"


class JSONImporter(GovernmentDataProvider):
    """Imports scheme data from verified JSON files in data/schemes/"""

    @property
    def source_name(self) -> str:
        return "Local JSON (Official Government Sources)"

    @property
    def source_url(self) -> str:
        return "https://www.myscheme.gov.in"

    async def verify_source(self) -> bool:
        return DATA_DIR.exists() and any(DATA_DIR.glob("*.json"))

    async def fetch_schemes(self) -> List[dict]:
        schemes = []
        if not DATA_DIR.exists():
            logger.warning(f"Data directory not found: {DATA_DIR}")
            return []

        for json_file in sorted(DATA_DIR.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        schemes.extend(data)
                    elif isinstance(data, dict) and "schemes" in data:
                        schemes.extend(data["schemes"])
                    else:
                        schemes.append(data)
                logger.info(f"Loaded {json_file.name}")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        return schemes

    async def fetch_scheme_details(self, scheme_id: str) -> Optional[dict]:
        schemes = await self.fetch_schemes()
        for s in schemes:
            if str(s.get("id", "")) == str(scheme_id) or s.get("slug") == scheme_id:
                return s
        return None
