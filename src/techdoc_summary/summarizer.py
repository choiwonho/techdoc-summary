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

VERSION_DIFF_SECTION_TITLES = {
    "conclusion": "Conclusion",
    "must-check": "Must Check",
    "config-checklist": "Configuration Checklist",
    "release-highlights": "Release Highlights",
}

VERSION_DIFF_SECTION_ORDER = [
    "conclusion",
    "must-check",
    "config-checklist",
    "release-highlights",
]


def summarize(
    source_id: str,
    display_name: str,
    documents: list[SourceDocument],
    generated_on: Optional[date] = None,
) -> SummaryReport:
    if _is_version_diff_report(documents):
        return _summarize_version_diff(
            source_id=source_id,
            display_name=display_name,
            documents=documents,
            generated_on=generated_on,
        )

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


def _summarize_version_diff(
    source_id: str,
    display_name: str,
    documents: list[SourceDocument],
    generated_on: Optional[date],
) -> SummaryReport:
    grouped: dict[str, list[SourceDocument]] = defaultdict(list)
    for document in documents:
        grouped[document.section].append(document)

    sections = [
        SummarySection(
            title=VERSION_DIFF_SECTION_TITLES[section_id],
            body=_version_diff_section_body(section_id, grouped.get(section_id, [])),
        )
        for section_id in VERSION_DIFF_SECTION_ORDER
    ]

    range_label = _version_range_label(documents)
    return SummaryReport(
        source_id=source_id,
        display_name=display_name,
        generated_on=generated_on or date.today(),
        sections=sections,
        source_links=_unique_links(documents),
        title_en=f"{display_name} {range_label} Upgrade Impact Report",
        title_ko=f"{display_name} {range_label} 업그레이드 영향 리포트",
        file_label=f"{source_id}-{_version_range_slug(range_label)}",
    )


def _section_body(section_id: str, documents: list[SourceDocument]) -> str:
    if not documents:
        title = SECTION_TITLES[section_id]
        return f"No official source content was collected for {title}."

    lines: list[str] = []
    for document in documents:
        lines.append(f"- {document.title}: {document.content}")
    return "\n".join(lines)


def _version_diff_section_body(section_id: str, documents: list[SourceDocument]) -> str:
    if not documents:
        title = VERSION_DIFF_SECTION_TITLES[section_id]
        return f"No curated version comparison content was collected for {title}."

    if section_id == "must-check":
        lines = [
            "| 항목 | 변경 내용 | 영향 | 해야 할 일 |",
            "|---|---|---|---|",
        ]
        for document in documents:
            lines.append(
                f"| {document.title} | {document.content} | {document.impact} | {document.action} |"
            )
        return "\n".join(lines)

    return "\n".join(f"- {document.content}" for document in documents)


def _unique_links(documents: list[SourceDocument]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for document in documents:
        if document.url not in seen:
            links.append(document.url)
            seen.add(document.url)
    return links


def _is_version_diff_report(documents: list[SourceDocument]) -> bool:
    return any(document.section in VERSION_DIFF_SECTION_TITLES for document in documents)


def _version_range_label(documents: list[SourceDocument]) -> str:
    for document in documents:
        if document.section == "conclusion" and document.title:
            return document.title
    return "Version Comparison"


def _version_range_slug(range_label: str) -> str:
    return range_label.replace(" -> ", "-to-").replace(" ", "-")
