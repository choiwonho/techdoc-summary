import pytest

from techdoc_summary.models import SourceDocument
from techdoc_summary.sources import UnknownSourceError, available_sources, get_adapter


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


def test_unknown_source_error_lists_available_sources():
    with pytest.raises(UnknownSourceError) as error:
        get_adapter("docker")

    assert "Unknown source 'docker'" in str(error.value)
    assert "elasticsearch" in str(error.value)
    assert "kafka" in str(error.value)
