from __future__ import annotations

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources.base import BaseSourceAdapter


class ElasticsearchAdapter(BaseSourceAdapter):
    source_id = "elasticsearch"
    display_name = "Elasticsearch"

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
                url="https://www.elastic.co/docs/release-notes/elasticsearch",
                section="release-notes",
                content=(
                    "Review official Elasticsearch release notes for major changes, "
                    "improvements, bug fixes, and known issues."
                ),
            ),
            SourceDocument(
                title="Elasticsearch breaking changes",
                url="https://www.elastic.co/docs/release-notes/elasticsearch/breaking-changes",
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
                url="https://www.elastic.co/docs/release-notes/elasticsearch",
                section="bug-fixes",
                content="Bug fixes are listed in the official Elasticsearch release notes.",
            ),
        ]
