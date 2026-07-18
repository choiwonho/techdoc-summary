from __future__ import annotations

from abc import ABC, abstractmethod

from techdoc_summary.models import SourceDocument


class BaseSourceAdapter(ABC):
    source_id: str
    display_name: str

    @abstractmethod
    def fetch(self) -> list[SourceDocument]:
        """Return official source documents converted into the common model."""
