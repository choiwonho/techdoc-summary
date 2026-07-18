from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Optional

from techdoc_summary.models import SourceDocument, SummaryReport, SummarySection


SECTION_TITLES = {
    "current-version": "Current Version",
    "release-notes": "Major Changes",
    "breaking-changes": "Breaking Changes",
    "configuration": "Configuration Notes",
    "bug-fixes": "Bug Fixes",
}

SECTION_ORDER = [
    "current-version",
    "release-notes",
    "breaking-changes",
    "configuration",
    "bug-fixes",
]


def summarize(
    source_id: str,
    display_name: str,
    documents: list[SourceDocument],
    generated_on: Optional[date] = None,
) -> SummaryReport:
    grouped: dict[str, list[SourceDocument]] = defaultdict(list)
    for document in documents:
        grouped[document.section].append(document)

    sections = [
        SummarySection(
            title=SECTION_TITLES[section_id],
            body=_section_body(section_id, grouped.get(section_id, [])),
        )
        for section_id in SECTION_ORDER
    ]

    return SummaryReport(
        source_id=source_id,
        display_name=display_name,
        generated_on=generated_on or date.today(),
        sections=sections,
        source_links=_unique_links(documents),
    )


def _section_body(section_id: str, documents: list[SourceDocument]) -> str:
    if not documents:
        title = SECTION_TITLES[section_id]
        return f"No official source content was collected for {title}."

    lines: list[str] = []
    for document in documents:
        lines.append(f"- {document.title}: {document.content}")
    return "\n".join(lines)


def _unique_links(documents: list[SourceDocument]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for document in documents:
        if document.url not in seen:
            links.append(document.url)
            seen.add(document.url)
    return links
