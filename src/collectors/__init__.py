"""Abstract base class for all data collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import Mention


class BaseCollector(ABC):
    """Interface that all data source collectors must implement."""

    @abstractmethod
    def collect(self) -> list[Mention]:
        """Fetch and return normalized mentions from the source."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the identifier for this data source."""
        ...
