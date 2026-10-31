"""
data.gov.in Data Provider

Integrates with Open Government Data (OGD) Platform India (data.gov.in)
API reference: https://data.gov.in/apis
"""
import logging
from typing import List, Optional, Dict, Any
import httpx

from app.government.base import GovernmentDataProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

DATA_GOV_BASE = "https://api.data.gov.in/resource"


class DataGovProvider(GovernmentDataProvider):
    """Data provider for data.gov.in open government datasets."""

    @property
    def source_name(self) -> str:
        return "data.gov.in (Open Government Data India)"

    @property
    def source_url(self) -> str:
        return "https://data.gov.in"

    async def verify_source(self) -> bool:
        """Verify reachability of data.gov.in API."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://data.gov.in")
                return resp.status_code < 500
        except Exception:
            return False

    async def fetch_schemes(self) -> List[dict]:
        """
        Fetch schemes catalog from data.gov.in.
        Requires DATA_GOV_API_KEY. If unconfigured, gracefully logs and returns empty list.
        """
        if not settings.data_gov_api_key:
            logger.info("DATA_GOV_API_KEY not configured – data.gov.in integration skipped")
            return []

        # Example OGD resource endpoint
        try:
            params = {
                "api-key": settings.data_gov_api_key,
                "format": "json",
                "limit": 100,
            }
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(f"{DATA_GOV_BASE}/catalog", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("records", [])
                else:
                    logger.warning(f"data.gov.in returned status {resp.status_code}")
                    return []
        except Exception as e:
            logger.error(f"data.gov.in fetch error: {e}")
            return []

    async def fetch_scheme_details(self, scheme_id: str) -> Optional[dict]:
        if not settings.data_gov_api_key:
            return None
        return None

