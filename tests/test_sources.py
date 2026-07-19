import pytest

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources import UnknownSourceError, available_sources, get_adapter
from techdoc_summary.sources.elasticsearch import ElasticsearchAdapter, _version_range as elastic_version_range
from techdoc_summary.sources.kafka import KafkaAdapter
from techdoc_summary.sources.logstash import LogstashAdapter, _version_range as logstash_version_range


def test_registry_exposes_mvp_sources():
    assert available_sources() == ["elasticsearch", "kafka", "logstash"]


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


def test_elasticsearch_adapter_fetches_version_range_documents():
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        if url == "https://www.elastic.co/docs/release-notes/elasticsearch":
            return """
            <html>
              <h2>9.2.0</h2>
              <h3>Highlights</h3>
              <p>Add remote index support to LOOKUP JOIN.</p>
              <p>New lucene 10.3.0 release improves vector search.</p>
              <h2>9.1.0</h2>
              <h3>Highlights</h3>
              <p>Enable direct IO for BBQ rescoring as a tech preview.</p>
              <h2>9.0.0</h2>
              <h3>Highlights</h3>
              <p>rank_vectors field type is now available for late-interaction ranking.</p>
            </html>
            """
        return "<html><h1>Extra official Elasticsearch material</h1></html>"

    adapter = ElasticsearchAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("9.0", "9.2")

    assert documents[0].title == "Elasticsearch 9.0 -> 9.2 release notes"
    assert documents[0].section == "source-material"
    assert "rank_vectors" in documents[0].content
    assert "LOOKUP JOIN" in documents[0].content
    assert fetched_urls[:4] == [
        "https://www.elastic.co/docs/release-notes/elasticsearch",
        "https://www.elastic.co/docs/release-notes/elasticsearch/breaking-changes",
        "https://www.elastic.co/docs/release-notes/elasticsearch/deprecations",
        "https://www.elastic.co/docs/release-notes/elasticsearch/known-issues",
    ]
    assert all(document.section == "source-material" for document in documents)


def test_elasticsearch_adapter_filters_auxiliary_documents_to_version_range():
    def fake_fetch(url: str) -> str:
        if url == "https://www.elastic.co/blog/whats-new-elastic-search-8-13-0":
            return "<html><p>8.13.0 added release blog improvements.</p></html>"
        return """
        <html>
          <h2>9.3.0</h2>
          <p>This 9.3.0 known issue should not be included.</p>
          <h2>8.13.0</h2>
          <p>Review 8.13.0 compatibility and configuration changes.</p>
          <h2>8.12.0</h2>
          <p>8.12.0 added query improvements.</p>
        </html>
        """

    adapter = ElasticsearchAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("8.12", "8.13")
    combined = "\n".join(document.content for document in documents)

    assert "8.13.0 compatibility" in combined
    assert "8.12.0 added" in combined
    assert "9.3.0 known issue" not in combined


def test_elasticsearch_adapter_uses_release_blogs_for_7_to_8_range():
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        if url == "https://www.elastic.co/blog/whats-new-elastic-7-17-0":
            return "<html><p>Upgrade Assistant adds deprecated API coverage for 8.0 upgrades.</p></html>"
        if url == "https://www.elastic.co/blog/whats-new-elastic-8-0-0":
            return "<html><p>Elastic 8.0 introduces native NLP support and streamlined security defaults.</p></html>"
        if url == "https://www.elastic.co/blog/whats-new-elastic-search-8-13-0":
            return "<html><p>Elasticsearch 8.13 adds Lucene 9.10 and Learning to Rank as technical preview.</p></html>"
        return """
        <html>
          <h2>9.3.0</h2>
          <p>This 9.3.0 known issue should not be included.</p>
          <h2>8.13.0</h2>
          <p>8.13.0 added query improvements.</p>
        </html>
        """

    adapter = ElasticsearchAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("7.17", "8.13")
    titles = [document.title for document in documents[:3]]
    combined = "\n".join(document.content for document in documents)

    assert titles == [
        "Elastic Stack 7.17 release announcement",
        "Elastic 8.0 release announcement",
        "Elastic Search 8.13 release announcement",
    ]
    assert not any(document.title.endswith("release notes") for document in documents)
    assert fetched_urls[:3] == [
        "https://www.elastic.co/docs/release-notes/elasticsearch",
        "https://www.elastic.co/blog/whats-new-elastic-7-17-0",
        "https://www.elastic.co/blog/whats-new-elastic-8-0-0",
    ]
    assert "Upgrade Assistant adds deprecated API coverage" in combined
    assert "native NLP support" in combined
    assert "Learning to Rank" in combined
    assert "9.3.0 known issue" not in combined


def test_elasticsearch_release_blog_excludes_page_navigation_text():
    def fake_fetch(url: str) -> str:
        if url == "https://www.elastic.co/blog/whats-new-elastic-search-8-13-0":
            return """
            <html>
              <nav>AutoOps Easy cluster management with performance recommendations.</nav>
              <article>
                <h1>Elastic Search 8.13</h1>
                <p>Share on Twitter Print this page.</p>
                <div class="section blog-title-text">
                <p>Elasticsearch 8.13 adds Lucene 9.10 and Learning to Rank as technical preview.</p>
                </div>
              </article>
            </html>
            """
        return "<html></html>"

    adapter = ElasticsearchAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("8.13", "8.13")
    blog_content = documents[0].content

    assert "Learning to Rank" in blog_content
    assert "AutoOps Easy cluster management" not in blog_content
    assert "Share on Twitter" not in blog_content


def test_elasticsearch_version_range_crosses_7_to_8_boundary():
    versions = elastic_version_range("7.17", "8.13")

    assert versions[0] == "7.17"
    assert versions[1] == "8.0"
    assert versions[-1] == "8.13"
    assert len(versions) == 15


def test_get_adapter_returns_kafka_adapter_documents():
    adapter = get_adapter("kafka")
    documents = adapter.fetch()

    assert adapter.source_id == "kafka"
    assert adapter.display_name == "Kafka"
    assert all(document.url.startswith("https://") for document in documents)


def test_get_adapter_returns_logstash_adapter_documents():
    adapter = get_adapter("logstash")
    documents = adapter.fetch()

    assert adapter.source_id == "logstash"
    assert adapter.display_name == "Logstash"
    assert all(isinstance(document, SourceDocument) for document in documents)
    assert {document.section for document in documents} >= {
        "current-version",
        "release-notes",
        "breaking-changes",
        "configuration",
        "bug-fixes",
    }


def test_logstash_version_range_crosses_7_to_8_boundary():
    versions = logstash_version_range("7.17", "8.13")

    assert versions[0] == "7.17"
    assert versions[1] == "8.0"
    assert versions[-1] == "8.13"
    assert len(versions) == 15


def test_logstash_adapter_fetches_major_boundary_documents():
    fetched_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        return f"""
        <html>
          <main>
            <h1>{url}</h1>
            <p>Logstash upgrade material added Java and ECS compatibility notes.</p>
          </main>
        </html>
        """

    adapter = LogstashAdapter(fetcher=fake_fetch)

    documents = adapter.fetch_version_diff("7.17", "8.13")

    assert [document.title for document in documents[:3]] == [
        "Logstash 7.17.0 release notes",
        "Logstash 8.0.0 release notes",
        "Logstash 8.13.0 release notes",
    ]
    assert fetched_urls[:3] == [
        "https://www.elastic.co/guide/en/logstash/7.17/logstash-7-17-0.html",
        "https://www.elastic.co/guide/en/logstash/8.19/logstash-8-0-0.html",
        "https://www.elastic.co/guide/en/logstash/8.13/logstash-8-13-0.html",
    ]
    assert "https://www.elastic.co/guide/en/logstash/8.13/upgrading-logstash.html" in fetched_urls
    assert any(document.title == "Logstash upgrade documentation" for document in documents)
    assert any(document.title == "Logstash 8.0 breaking changes" for document in documents)
    assert all(document.section == "source-material" for document in documents)


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
