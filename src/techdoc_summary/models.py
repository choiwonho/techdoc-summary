from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceDocument:
    title: str
    url: str
    content: str
    section: str
    impact: str = ""
    action: str = ""


@dataclass(frozen=True)
class SummarySection:
    title: str
    body: str
    body_ko: str | None = None


@dataclass(frozen=True)
class SummaryReport:
    source_id: str
    display_name: str
    generated_on: date
    sections: list[SummarySection]
    source_links: list[str]
    title_en: str | None = None
    title_ko: str | None = None
    file_label: str | None = None
