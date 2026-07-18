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

    def fetch_version_diff(self, from_version: str, to_version: str) -> list[SourceDocument]:
        if (from_version, to_version) != ("3.8", "4.1"):
            return [
                SourceDocument(
                    title=f"Kafka {from_version} to {to_version} comparison",
                    url="https://kafka.apache.org/documentation/#upgrade",
                    section="current-version",
                    content=(
                        f"No curated Kafka comparison findings are available for "
                        f"{from_version} -> {to_version}. Review the official upgrade "
                        "notes and release notes before planning the upgrade."
                    ),
                )
            ]

        return [
            SourceDocument(
                title="Kafka 3.8 to 4.1 upgrade posture",
                url="https://kafka.apache.org/documentation/#upgrade",
                section="current-version",
                content=(
                    "Kafka 3.8에서 4.1로 이동하는 작업은 major-version upgrade로 "
                    "다뤄야 합니다. 패치 업데이트처럼 적용하기보다 브로커, 클라이언트, "
                    "Kafka Streams, Connect, 운영 도구의 호환성을 함께 점검해야 합니다."
                ),
            ),
            SourceDocument(
                title="Kafka 4.x major changes",
                url="https://kafka.apache.org/downloads",
                section="release-notes",
                content=(
                    "Kafka 4.x 범위에서는 런타임과 운영 방식의 오래된 호환성 경로가 "
                    "정리될 수 있으므로 릴리스 노트에서 새 기능보다 제거된 동작, 변경된 "
                    "기본값, 프로토콜 및 클라이언트 호환성 항목을 우선 확인해야 합니다."
                ),
            ),
            SourceDocument(
                title="Kafka 4.x upgrade cautions",
                url="https://kafka.apache.org/documentation/#upgrade",
                section="breaking-changes",
                content=(
                    "ZooKeeper 기반 운영을 전제로 한 절차, 스크립트, 모니터링, 장애 대응 "
                    "문서는 4.x 업그레이드 전에 다시 검증해야 합니다. 브로커 롤링 업그레이드 "
                    "순서와 클라이언트 호환성 매트릭스를 먼저 확정하는 것이 안전합니다."
                ),
            ),
            SourceDocument(
                title="Kafka configuration review",
                url="https://kafka.apache.org/documentation/#configuration",
                section="configuration",
                content=(
                    "운영 설정에서는 deprecated 옵션, 제거된 설정, 변경된 기본값을 "
                    "확인해야 합니다. server.properties, client 설정, Connect worker 설정, "
                    "Streams 애플리케이션 설정을 나눠서 비교하는 방식이 좋습니다."
                ),
            ),
            SourceDocument(
                title="Kafka fixes and improvements",
                url="https://kafka.apache.org/downloads",
                section="bug-fixes",
                content=(
                    "3.8 이후 4.1까지의 개선 사항은 단순 버그 수정뿐 아니라 성능, 안정성, "
                    "운영 가시성 개선을 포함할 수 있습니다. 실제 적용 전에는 현재 장애 회피용 "
                    "workaround가 새 버전에서도 필요한지 확인해야 합니다."
                ),
            ),
        ]
