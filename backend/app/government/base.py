"""
Government Data Provider – Abstract Base Class

All government data providers must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class GovernmentDataProvider(ABC):
    """Abstract base class for government scheme data sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of this data source."""
        ...

    @property
    @abstractmethod
    def source_url(self) -> str:
        """Official URL of the data source."""
        ...

    @abstractmethod
    async def fetch_schemes(self) -> List[dict]:
        """
        Fetch all schemes from the government source.
        Returns a list of scheme dicts conforming to our schema.
        """
        ...

    @abstractmethod
    async def fetch_scheme_details(self, scheme_id: str) -> Optional[dict]:
        """Fetch details for a specific scheme."""
        ...

    async def verify_source(self) -> bool:
        """Check if the source is reachable. Returns True if accessible."""
        return False

    async def update_scheme(self, scheme_id: str) -> Optional[dict]:
        """Refresh a single scheme's data from the source."""
        return await self.fetch_scheme_details(scheme_id)
