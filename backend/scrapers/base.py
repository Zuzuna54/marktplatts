from abc import ABC, abstractmethod


class BaseScraper(ABC):
    source_id: str           # e.g. "marktplaats", "autoscout24"
    source_display: str      # e.g. "Marktplaats", "AutoScout24"

    @abstractmethod
    async def full_sync(self) -> int:
        """Run a full sync. Returns total listings fetched."""

    @abstractmethod
    async def incremental_sync(self) -> int:
        """Fetch only new/updated listings since last sync. Returns count."""
