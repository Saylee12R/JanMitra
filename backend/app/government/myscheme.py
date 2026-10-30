"""
myScheme.gov.in Data Provider

myScheme is the official government portal for scheme discovery.
API reference: https://www.myscheme.gov.in/

NOTE: The myScheme public API endpoints may require registration.
If not available, use the JSON importer instead.
"""
import logging
from typing import List, Optional

import httpx

from app.government.base import GovernmentDataProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MY_SCHEME_BASE = "https://www.myscheme.gov.in/api"


class MySchemeProvider(GovernmentDataProvider):
    """Data provider for myScheme.gov.in"""

    @property
    def source_name(self) -> str:
        return "myScheme (Government of India)"

    @property
    def source_url(self) -> str:
        return "https://www.myscheme.gov.in"

    async def verify_source(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(MY_SCHEME_BASE)
                return resp.status_code < 500
        except Exception:
            return False

    async def fetch_schemes(self) -> List[dict]:
        """
        Fetch schemes from myScheme API.
        Requires MY_SCHEME_API_KEY if API is behind auth.
        """
        if not settings.my_scheme_api_key:
            logger.warning("MY_SCHEME_API_KEY not configured – skipping myScheme fetch")
            return []

        try:
            headers = {"Authorization": f"Bearer {settings.my_scheme_api_key}"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{MY_SCHEME_BASE}/schemes", headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data.get("schemes", [])
        except Exception as e:
            logger.error(f"myScheme fetch error: {e}")
            return []

    async def fetch_scheme_details(self, scheme_id: str) -> Optional[dict]:
        if not settings.my_scheme_api_key:
            return None
        try:
            headers = {"Authorization": f"Bearer {settings.my_scheme_api_key}"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{MY_SCHEME_BASE}/schemes/{scheme_id}", headers=headers
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"myScheme detail fetch error: {e}")
            return None
