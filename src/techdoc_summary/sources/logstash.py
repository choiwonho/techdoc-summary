from __future__ import annotations

import re
from collections.abc import Callable
from html import unescape

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources.base import BaseSourceAdapter
from techdoc_summary.sources.http import fetch_text


LOGSTASH_DOCS_URL = "https://www.elastic.co/guide/en/logstash/current/index.html"
LOGSTASH_RELEASE_NOTES_URL = (
    "https://www.elastic.co/guide/en/logstash/current/releasenotes.html"
)
LOGSTASH_UPGRADE_URL = "https://www.elastic.co/guide/en/logstash/current/upgrading-logstash.html"
LOGSTASH_8_BREAKING_CHANGES_URL = (
    "https://www.elastic.co/guide/en/logstash/8.19/breaking-8.0.html"
)
LOGSTASH_CONFIGURATION_URL = (
    "https://www.elastic.co/guide/en/logstash/current/configuration.html"
)


class LogstashAdapter(BaseSourceAdapter):
    source_id = "logstash"
    display_name = "Logstash"

    def __init__(self, fetcher: Callable[[str], str] = fetch_text) -> None:
        self._fetcher = fetcher

    def fetch(self) -> list[SourceDocument]:
        return [
            SourceDocument(
                title="Logstash documentation",
                url=LOGSTASH_DOCS_URL,
                section="current-version",
                content=(
                    "Use the official Logstash documentation to confirm the current "
                    "release line, pipeline behavior, and supported configuration."
                ),
            ),
            SourceDocument(
                title="Logstash release notes",
                url=LOGSTASH_RELEASE_NOTES_URL,
                section="release-notes",
                content=(
                    "Review official Logstash release notes for major changes, "
                    "improvements, plugin updates, and known issues."
                ),
            ),
            SourceDocument(
                title="Logstash breaking changes",
                url=LOGSTASH_8_BREAKING_CHANGES_URL,
                section="breaking-changes",
                content="Review Logstash breaking changes before upgrading major versions.",
            ),
            SourceDocument(
                title="Logstash configuration",
                url=LOGSTASH_CONFIGURATION_URL,
                section="configuration",
                content=(
                    "Use the Logstash configuration reference to understand pipeline, "
                    "plugin, queue, ECS, SSL, and JVM settings."
                ),
            ),
            SourceDocument(
                title="Logstash bug fixes",
                url=LOGSTASH_RELEASE_NOTES_URL,
                section="bug-fixes",
                content="Bug fixes are listed in the official Logstash release notes.",
            ),
        ]

    def fetch_version_diff(self, from_version: str, to_version: str) -> list[SourceDocument]:
        versions = _version_range(from_version, to_version)
        document_versions = _high_signal_versions(versions)
        documents = [
            _source_document(
                f"Logstash {version}.0 release notes",
                _release_note_url(version),
                self._fetcher(_release_note_url(version)),
            )
            for version in document_versions
        ]
        documents.extend(
            [
                _source_document(
                    "Logstash upgrade documentation",
                    _upgrade_url(to_version),
                    self._fetcher(_upgrade_url(to_version)),
                ),
                _source_document(
                    "Logstash 8.0 breaking changes",
                    LOGSTASH_8_BREAKING_CHANGES_URL,
                    self._fetcher(LOGSTASH_8_BREAKING_CHANGES_URL),
                ),
            ]
        )
        return [document for document in documents if document.content]


def _version_range(from_version: str, to_version: str) -> list[str]:
    start_major, start_minor = _parse_version(from_version)
    end_major, end_minor = _parse_version(to_version)
    if (start_major, start_minor) > (end_major, end_minor):
        raise ValueError("from-version must be less than or equal to to-version")

    versions: list[str] = []
    major = start_major
    minor = start_minor
    while (major, minor) <= (end_major, end_minor):
        versions.append(f"{major}.{minor}")
        minor += 1
        if major == 7 and minor > 17:
            major = 8
            minor = 0
        if major == 8 and minor > 19:
            major = 9
            minor = 0
    return versions


def _parse_version(version: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Unsupported Logstash version format: {version}")
    return int(match.group(1)), int(match.group(2))


def _high_signal_versions(versions: list[str]) -> list[str]:
    selected: list[str] = []
    for version in (versions[0], *versions[1:-1], versions[-1]):
        major = version.split(".", maxsplit=1)[0]
        if version in {versions[0], versions[-1]} or version.endswith(".0"):
            selected.append(version)
        elif major not in {item.split(".", maxsplit=1)[0] for item in selected}:
            selected.append(version)
    return list(dict.fromkeys(selected))


def _release_note_url(version: str) -> str:
    major, minor = _parse_version(version)
    doc_version = "8.19" if major == 8 and minor == 0 else version
    page_version = version.replace(".", "-")
    return (
        f"https://www.elastic.co/guide/en/logstash/{doc_version}/"
        f"logstash-{page_version}-0.html"
    )


def _upgrade_url(version: str) -> str:
    return f"https://www.elastic.co/guide/en/logstash/{version}/upgrading-logstash.html"


def _source_document(title: str, url: str, html: str) -> SourceDocument:
    return SourceDocument(
        title=title,
        url=url,
        section="source-material",
        content=_html_to_text(html),
    )


def _html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
