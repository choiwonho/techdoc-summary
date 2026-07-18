from __future__ import annotations

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources.base import BaseSourceAdapter


class KafkaAdapter(BaseSourceAdapter):
    source_id = "kafka"
    display_name = "Kafka"

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
