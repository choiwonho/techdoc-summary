from techdoc_summary.models import SourceDocument
from techdoc_summary.version_reporter import generate_version_diff_report


def test_generate_version_diff_report_extracts_official_change_sentences():
    documents = [
        SourceDocument(
            title="Kafka 4.1.0 release announcement",
            url="https://kafka.apache.org/blog/2025/09/04/apache-kafka-4.1.0-release-announcement/",
            section="source-material",
            content=(
                "Apache Kafka 4.1.0 added Queues for Kafka as a preview feature. "
                "The release introduced Streams rebalance protocol as early access. "
                "This unrelated sentence should be ignored."
            ),
        ),
        SourceDocument(
            title="Kafka upgrade documentation",
            url="https://kafka.apache.org/documentation/#upgrade",
            section="source-material",
            content=(
                "ZooKeeper mode was removed and KRaft mode is required. "
                "The default configuration changed for producer linger.ms."
            ),
        ),
    ]

    report = generate_version_diff_report(
        source_id="kafka",
        display_name="Kafka",
        from_version="3.9",
        to_version="4.1",
        documents=documents,
    )

    assert report.title_ko == "Kafka 3.9 -> 4.1 업그레이드 영향 리포트"
    assert report.file_label == "kafka-3.9-to-4.1"
    combined_en = "\n".join(section.body for section in report.sections)
    combined_ko = "\n".join(section.body_ko or "" for section in report.sections)
    assert "Queues for Kafka" in combined_en
    assert "ZooKeeper mode was removed" in combined_en
    assert "| 항목 | 변경 내용 | 영향 | 해야 할 일 |" in combined_ko
    assert "설정" in combined_ko


def test_generate_version_diff_report_filters_navigation_and_promo_noise():
    documents = [
        SourceDocument(
            title="Kafka 4.0.0 release announcement",
            url="https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/",
            section="source-material",
            content=(
                "Apache Kafka 4.0.0 Release Announcement | Apache Kafka Get Started Introduction Quickstart Use Cases Books and Papers Videos Podcasts Docs Key Concepts APIs Configuration. "
                "We want to take this as an opportunity to express our gratitude to the ZooKeeper community and say thank you! "
                "Apache Kafka 4.0 is a significant milestone, marking the first major release to operate entirely without Apache ZooKeeper. "
            ),
        )
    ]

    report = generate_version_diff_report(
        source_id="kafka",
        display_name="Kafka",
        from_version="3.9",
        to_version="4.0",
        documents=documents,
    )

    combined = "\n".join(section.body for section in report.sections)
    assert "Get Started Introduction Quickstart" not in combined
    assert "express our gratitude" not in combined
    assert "operate entirely without Apache ZooKeeper" in combined
