from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceDocument:
    title: str
    url: str
    content: str
    section: str


@dataclass(frozen=True)
class SummarySection:
    title: str
    body: str


@dataclass(frozen=True)
class SummaryReport:
    source_id: str
    display_name: str
    generated_on: date
    sections: list[SummarySection]
    source_links: list[str]
