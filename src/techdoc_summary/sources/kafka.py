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
                    "Kafka 3.8에서 4.1로 이동할 때 핵심 변화는 4.0 경계입니다. "
                    "Kafka 4.x는 ZooKeeper 모드를 지원하지 않고 KRaft 모드가 필수입니다. "
                    "현재 클러스터가 ZooKeeper 기반이면 4.1 업그레이드 전에 KRaft 마이그레이션을 "
                    "먼저 끝내야 하며, 3.8에서 바로 4.1 바이너리만 교체하는 방식으로 접근하면 안 됩니다."
                ),
            ),
            SourceDocument(
                title="Kafka 4.x major changes",
                url="https://kafka.apache.org/downloads",
                section="release-notes",
                content=(
                    "4.0에서 오래된 protocol API 버전과 deprecated API가 제거됐습니다. "
                    "Java client, Kafka Streams, Connect는 2.1 이상이어야 4.0 브로커와의 "
                    "호환성을 기대할 수 있고, 사내 wrapper나 비공식 Kafka client도 KIP-896 "
                    "영향을 따로 확인해야 합니다. 4.1에서는 Queues for Kafka(KIP-932)가 preview로 "
                    "추가되고 Streams rebalance protocol(KIP-1071)이 early access로 들어왔지만, "
                    "둘 다 운영 기본 기능으로 바로 켜기보다 별도 검증 대상으로 보는 편이 안전합니다."
                ),
            ),
            SourceDocument(
                title="Kafka 4.x upgrade cautions",
                url="https://kafka.apache.org/documentation/#upgrade",
                section="breaking-changes",
                content=(
                    "SASL/OAUTHBEARER를 쓰는 경우 보안 callback handler 참조를 확인해야 합니다. "
                    "org.apache.kafka.common.security.oauthbearer.secured 패키지의 "
                    "OAuthBearerLoginCallbackHandler와 OAuthBearerValidatorCallbackHandler는 제거됐고, "
                    "secured가 빠진 org.apache.kafka.common.security.oauthbearer 패키지의 클래스를 "
                    "사용해야 합니다. 또한 Kafka 4.0부터 sasl.oauthbearer token/JWKS endpoint를 "
                    "허용하려면 org.apache.kafka.sasl.oauthbearer.allowed.urls 시스템 속성 검토가 필요합니다."
                ),
            ),
            SourceDocument(
                title="Kafka configuration review",
                url="https://kafka.apache.org/documentation/#configuration",
                section="configuration",
                content=(
                    "server.properties와 client 설정에서 제거 또는 기본값 변경 항목을 점검해야 합니다. "
                    "log.message.format.version과 message.format.version은 제거됐고, "
                    "delegation.token.master.key는 delegation.token.secret.key로 바꿔야 합니다. "
                    "producer 기본 linger.ms는 0에서 5로 변경됐으며, enable.idempotence는 "
                    "max.in.flight.requests.per.connection 값이 5를 초과해도 예전처럼 자동 fallback하지 않습니다. "
                    "4.1에서는 log.cleaner.enable이 deprecated 됐고 false 설정을 더 이상 유지하지 않는 방향으로 준비해야 합니다."
                ),
            ),
            SourceDocument(
                title="Kafka fixes and improvements",
                url="https://kafka.apache.org/downloads",
                section="bug-fixes",
                content=(
                    "런타임 요구사항도 같이 올라갑니다. Kafka 4.0부터 client와 Kafka Streams "
                    "애플리케이션의 최소 Java 버전은 Java 11이고, broker, Connect, tools는 Java 17이 필요합니다. "
                    "4.1.1에는 Kafka Streams의 메모리 누수와 데이터 손실 관련 중요 수정이 포함됐고, "
                    "4.1.2에는 producer record가 잘못된 topic으로 갈 수 있는 드문 버그 수정이 포함됐습니다. "
                    "따라서 4.1 계열을 쓸 때는 가능하면 최신 4.1.x 패치 버전까지 함께 검토하는 것이 좋습니다."
                ),
            ),
        ]
