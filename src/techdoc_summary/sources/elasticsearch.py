from __future__ import annotations

import re
from collections.abc import Callable
from html import unescape

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources.base import BaseSourceAdapter
from techdoc_summary.sources.http import fetch_text


ELASTICSEARCH_RELEASE_NOTES_URL = "https://www.elastic.co/docs/release-notes/elasticsearch"
ELASTICSEARCH_BREAKING_CHANGES_URL = (
    "https://www.elastic.co/docs/release-notes/elasticsearch/breaking-changes"
)
ELASTICSEARCH_DEPRECATIONS_URL = (
    "https://www.elastic.co/docs/release-notes/elasticsearch/deprecations"
)
ELASTICSEARCH_KNOWN_ISSUES_URL = (
    "https://www.elastic.co/docs/release-notes/elasticsearch/known-issues"
)

ELASTICSEARCH_RELEASE_BLOGS = {
    "7.17": (
        "Elastic Stack 7.17 release announcement",
        "https://www.elastic.co/blog/whats-new-elastic-7-17-0",
    ),
    "8.0": (
        "Elastic 8.0 release announcement",
        "https://www.elastic.co/blog/whats-new-elastic-8-0-0",
    ),
    "8.13": (
        "Elastic Search 8.13 release announcement",
        "https://www.elastic.co/blog/whats-new-elastic-search-8-13-0",
    ),
}


class ElasticsearchAdapter(BaseSourceAdapter):
    source_id = "elasticsearch"
    display_name = "Elasticsearch"

    def __init__(self, fetcher: Callable[[str], str] = fetch_text) -> None:
        self._fetcher = fetcher

    def fetch(self) -> list[SourceDocument]:
        return [
            SourceDocument(
                title="Elasticsearch documentation",
                url="https://www.elastic.co/docs",
                section="current-version",
                content=(
                    "Use the official Elasticsearch documentation to confirm the "
                    "current release line and supported versions."
                ),
            ),
            SourceDocument(
                title="Elasticsearch release notes",
                url=ELASTICSEARCH_RELEASE_NOTES_URL,
                section="release-notes",
                content=(
                    "Review official Elasticsearch release notes for major changes, "
                    "improvements, bug fixes, and known issues."
                ),
            ),
            SourceDocument(
                title="Elasticsearch breaking changes",
                url=ELASTICSEARCH_BREAKING_CHANGES_URL,
                section="breaking-changes",
                content="Review breaking changes before upgrading Elasticsearch clusters.",
            ),
            SourceDocument(
                title="Elasticsearch configuration",
                url="https://www.elastic.co/docs/reference/elasticsearch/configuration-reference",
                section="configuration",
                content=(
                    "Use the configuration reference to understand Elasticsearch "
                    "settings and operational impact."
                ),
            ),
            SourceDocument(
                title="Elasticsearch bug fixes",
                url=ELASTICSEARCH_RELEASE_NOTES_URL,
                section="bug-fixes",
                content="Bug fixes are listed in the official Elasticsearch release notes.",
            ),
        ]

    def fetch_version_diff(self, from_version: str, to_version: str) -> list[SourceDocument]:
        versions = _version_range(from_version, to_version)
        release_notes_text = _html_to_text(self._fetcher(ELASTICSEARCH_RELEASE_NOTES_URL))
        release_notes_content = _extract_version_sections(release_notes_text, versions)
        documents = [
            _source_document(title, url, self._fetcher(url))
            for version in versions
            if version in ELASTICSEARCH_RELEASE_BLOGS
            for title, url in [ELASTICSEARCH_RELEASE_BLOGS[version]]
        ]
        if not documents:
            documents.append(
                SourceDocument(
                    title=f"Elasticsearch {from_version} -> {to_version} release notes",
                    url=ELASTICSEARCH_RELEASE_NOTES_URL,
                    section="source-material",
                    content=release_notes_content,
                )
            )
        documents.extend(
            document
            for document in [
                _version_filtered_source_document(
                    "Elasticsearch breaking changes",
                    ELASTICSEARCH_BREAKING_CHANGES_URL,
                    self._fetcher(ELASTICSEARCH_BREAKING_CHANGES_URL),
                    versions,
                ),
                _version_filtered_source_document(
                    "Elasticsearch deprecations",
                    ELASTICSEARCH_DEPRECATIONS_URL,
                    self._fetcher(ELASTICSEARCH_DEPRECATIONS_URL),
                    versions,
                ),
                _version_filtered_source_document(
                    "Elasticsearch known issues",
                    ELASTICSEARCH_KNOWN_ISSUES_URL,
                    self._fetcher(ELASTICSEARCH_KNOWN_ISSUES_URL),
                    versions,
                ),
            ]
            if document is not None
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
        raise ValueError(f"Unsupported Elasticsearch version format: {version}")
    return int(match.group(1)), int(match.group(2))


def _extract_version_sections(text: str, versions: list[str]) -> str:
    wanted = tuple(f"{version}." for version in versions)
    matches = list(re.finditer(r"\b(\d+\.\d+\.\d+)\b", text))
    chunks: list[str] = []
    for index, match in enumerate(matches):
        version = match.group(1)
        if not version.startswith(wanted):
            continue
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunks.append(text[start:end].strip())
    return "\n\n".join(chunks)


def _source_document(title: str, url: str, html: str) -> SourceDocument:
    return SourceDocument(
        title=title,
        url=url,
        section="source-material",
        content=_html_to_text(
            _extract_elastic_blog_article(html) if _is_elastic_blog(url) else html
        ),
    )


def _is_elastic_blog(url: str) -> bool:
    return "elastic.co/blog/" in url


def _extract_elastic_blog_article(html: str) -> str:
    match = re.search(r"<article\b.*?</article>", html, flags=re.IGNORECASE | re.DOTALL)
    article = match.group(0) if match else html
    body_start = re.search(
        r'<div class="[^"]*\bsection\b[^"]*\bblog-title-text\b',
        article,
        flags=re.IGNORECASE,
    )
    return article[body_start.start() :] if body_start else article


def _version_filtered_source_document(
    title: str,
    url: str,
    html: str,
    versions: list[str],
) -> SourceDocument | None:
    text = _html_to_text(html)
    content = _extract_version_sections(text, versions)
    if not content:
        return None
    return SourceDocument(
        title=title,
        url=url,
        section="source-material",
        content=content,
    )


def _html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
