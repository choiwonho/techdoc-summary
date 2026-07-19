from __future__ import annotations

import re
from html import unescape
from collections.abc import Callable

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources.base import BaseSourceAdapter
from techdoc_summary.sources.http import fetch_text


KAFKA_RELEASE_ANNOUNCEMENTS = {
    "3.7": (
        "Kafka 3.7.0 release announcement",
        "https://kafka.apache.org/blog/2024/02/27/apache-kafka-3.7.0-release-announcement/",
    ),
    "3.8": (
        "Kafka 3.8.0 release announcement",
        "https://kafka.apache.org/blog/2024/07/29/apache-kafka-3.8.0-release-announcement/",
    ),
    "3.9": (
        "Kafka 3.9.0 release announcement",
        "https://kafka.apache.org/blog/2024/11/06/apache-kafka-3.9.0-release-announcement/",
    ),
    "4.0": (
        "Kafka 4.0.0 release announcement",
        "https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/",
    ),
    "4.1": (
        "Kafka 4.1.0 release announcement",
        "https://kafka.apache.org/blog/2025/09/04/apache-kafka-4.1.0-release-announcement/",
    ),
}

KAFKA_BLOG_INDEX_URL = "https://kafka.apache.org/blog/"


class KafkaAdapter(BaseSourceAdapter):
    source_id = "kafka"
    display_name = "Kafka"

    def __init__(self, fetcher: Callable[[str], str] = fetch_text) -> None:
        self._fetcher = fetcher
        self._release_index: dict[str, tuple[str, str]] | None = None

    def fetch(self) -> list[SourceDocument]:
        return [
            SourceDocument(
                title="Apache Kafka documentation",
                url="https://kafka.apache.org/documentation/",
                section="current-version",
                content=(
                    "Use the official Kafka documentation to confirm the current "
                    "release line and configuration reference."
                ),
            ),
            SourceDocument(
                title="Apache Kafka downloads",
                url="https://kafka.apache.org/downloads",
                section="release-notes",
                content=(
                    "Use official Kafka downloads and release notes to review "
                    "released versions and changes."
                ),
            ),
            SourceDocument(
                title="Apache Kafka upgrade notes",
                url="https://kafka.apache.org/documentation/#upgrade",
                section="breaking-changes",
                content="Review Kafka upgrade notes before changing broker or client versions.",
            ),
            SourceDocument(
                title="Apache Kafka configuration",
                url="https://kafka.apache.org/documentation/#configuration",
                section="configuration",
                content=(
                    "Use the Kafka configuration reference to understand broker, "
                    "producer, consumer, and topic settings."
                ),
            ),
            SourceDocument(
                title="Apache Kafka release notes",
                url="https://kafka.apache.org/downloads",
                section="bug-fixes",
                content=(
                    "Bug fixes and improvements are linked from official Kafka "
                    "release artifacts and notes."
                ),
            ),
        ]

    def fetch_version_diff(self, from_version: str, to_version: str) -> list[SourceDocument]:
        versions = _version_range(from_version, to_version)
        documents = []
        for version in versions:
            release = self._release_announcement_for(version)
            if release is None:
                continue
            title, url = release
            documents.append(_source_document(title, url, self._fetcher(url)))
        documents.extend(
            [
                _source_document(
                    "Kafka upgrade documentation",
                    "https://kafka.apache.org/documentation/#upgrade",
                    self._fetcher("https://kafka.apache.org/documentation/#upgrade"),
                ),
                _source_document(
                    "Kafka compatibility documentation",
                    "https://kafka.apache.org/40/getting-started/compatibility/",
                    self._fetcher("https://kafka.apache.org/40/getting-started/compatibility/"),
                ),
            ]
        )
        return documents

    def _release_announcement_for(self, version: str) -> tuple[str, str] | None:
        if version in KAFKA_RELEASE_ANNOUNCEMENTS:
            return KAFKA_RELEASE_ANNOUNCEMENTS[version]
        if self._release_index is None:
            self._release_index = _parse_release_index(self._fetcher(KAFKA_BLOG_INDEX_URL))
        return self._release_index.get(version)


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
        if major == 3 and minor > 9:
            major = 4
            minor = 0
    return versions


def _parse_version(version: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Unsupported Kafka version format: {version}")
    return int(match.group(1)), int(match.group(2))


def _source_document(title: str, url: str, html: str) -> SourceDocument:
    return SourceDocument(
        title=title,
        url=url,
        section="source-material",
        content=_html_to_text(html),
    )


def _parse_release_index(html: str) -> dict[str, tuple[str, str]]:
    releases: dict[str, tuple[str, str]] = {}
    for href, version, minor_version in re.findall(
        r'href=["\']?([^"\' >]*apache-kafka-((\d+\.\d+)\.\d+)-release-announcement/?)',
        html,
        flags=re.IGNORECASE,
    ):
        if minor_version in releases:
            continue
        url = _absolute_kafka_url(href)
        releases[minor_version] = (f"Kafka {version} release announcement", url)
    return releases


def _absolute_kafka_url(href: str) -> str:
    if href.startswith("https://"):
        return href
    if href.startswith("/"):
        return f"https://kafka.apache.org{href}"
    return f"https://kafka.apache.org/blog/{href}"


def _html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
