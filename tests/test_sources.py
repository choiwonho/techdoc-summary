import pytest

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources import UnknownSourceError, available_sources, get_adapter
from techdoc_summary.sources.kafka import KafkaAdapter


def test_registry_exposes_mvp_sources():
    assert available_sources() == ["elasticsearch", "kafka"]


def test_get_adapter_returns_elasticsearch_adapter_documents():
    adapter = get_adapter("elasticsearch")
    documents = adapter.fetch()

    assert adapter.source_id == "elasticsearch"
    assert adapter.display_name == "Elasticsearch"
    assert all(isinstance(document, SourceDocument) for document in documents)
    assert {document.section for document in documents} >= {
        "current-version",
        "release-notes",
        "breaking-changes",
        "configuration",
        "bug-fixes",
    }


def test_get_adapter_returns_kafka_adapter_documents():
    adapter = get_adapter("kafka")
    documents = adapter.fetch()

    assert adapter.source_id == "kafka"
    assert adapter.display_name == "Kafka"
    assert all(document.url.startswith("https://") for document in documents)


def test_kafka_adapter_returns_version_diff_documents_for_3_8_to_4_1():
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        return f"<html><h1>{url}</h1><p>Kafka upgrade material</p></html>"

    adapter = KafkaAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("3.8", "4.1")

    assert [document.title for document in documents[:4]] == [
        "Kafka 3.8.0 release announcement",
        "Kafka 3.9.0 release announcement",
        "Kafka 4.0.0 release announcement",
        "Kafka 4.1.0 release announcement",
    ]
    assert fetched_urls[:4] == [
        "https://kafka.apache.org/blog/2024/07/29/apache-kafka-3.8.0-release-announcement/",
        "https://kafka.apache.org/blog/2024/11/06/apache-kafka-3.9.0-release-announcement/",
        "https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/",
        "https://kafka.apache.org/blog/2025/09/04/apache-kafka-4.1.0-release-announcement/",
    ]
    assert all(document.section == "source-material" for document in documents)


def test_kafka_adapter_fetches_official_documents_for_any_version_range():
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        return f"<html><h1>{url}</h1><p>Release content for {url}</p></html>"

    adapter = KafkaAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("3.7", "3.9")

    assert [document.title for document in documents] == [
        "Kafka 3.7.0 release announcement",
        "Kafka 3.8.0 release announcement",
        "Kafka 3.9.0 release announcement",
        "Kafka upgrade documentation",
        "Kafka compatibility documentation",
    ]
    assert fetched_urls[:3] == [
        "https://kafka.apache.org/blog/2024/02/27/apache-kafka-3.7.0-release-announcement/",
        "https://kafka.apache.org/blog/2024/07/29/apache-kafka-3.8.0-release-announcement/",
        "https://kafka.apache.org/blog/2024/11/06/apache-kafka-3.9.0-release-announcement/",
    ]
    assert all(document.section == "source-material" for document in documents)
    assert all("Release content" in document.content for document in documents)


def test_kafka_adapter_discovers_unmapped_release_from_blog_index():
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        if url == "https://kafka.apache.org/blog/":
            return """
            <html>
              <a href=/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/>
                Apache Kafka 4.2.0 Release Announcement
              </a>
            </html>
            """
        return f"<html><p>Release content for {url}</p></html>"

    adapter = KafkaAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("4.2", "4.2")

    assert documents[0].title == "Kafka 4.2.0 release announcement"
    assert documents[0].url == (
        "https://kafka.apache.org/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/"
    )
    assert fetched_urls[:2] == [
        "https://kafka.apache.org/blog/",
        "https://kafka.apache.org/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/",
    ]


def test_unknown_source_error_lists_available_sources():
    with pytest.raises(UnknownSourceError) as error:
        get_adapter("docker")

    assert "Unknown source 'docker'" in str(error.value)
    assert "elasticsearch" in str(error.value)
    assert "kafka" in str(error.value)
