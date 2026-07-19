from __future__ import annotations

from techdoc_summary.sources.base import BaseSourceAdapter
from techdoc_summary.sources.elasticsearch import ElasticsearchAdapter
from techdoc_summary.sources.kafka import KafkaAdapter
from techdoc_summary.sources.logstash import LogstashAdapter


class UnknownSourceError(ValueError):
    def __init__(self, source_id: str, available: list[str]) -> None:
        self.source_id = source_id
        self.available = available
        super().__init__(
            f"Unknown source '{source_id}'. Available sources: {', '.join(available)}"
        )


_ADAPTERS: dict[str, type[BaseSourceAdapter]] = {
    ElasticsearchAdapter.source_id: ElasticsearchAdapter,
    KafkaAdapter.source_id: KafkaAdapter,
    LogstashAdapter.source_id: LogstashAdapter,
}


def available_sources() -> list[str]:
    return sorted(_ADAPTERS)


def get_adapter(source_id: str) -> BaseSourceAdapter:
    try:
        adapter_class = _ADAPTERS[source_id]
    except KeyError as exc:
        raise UnknownSourceError(source_id, available_sources()) from exc
    return adapter_class()
