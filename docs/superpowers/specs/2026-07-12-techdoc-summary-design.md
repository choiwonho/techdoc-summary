# Techdoc Summary Design

## Path

```markdown
<project-root>
```

## Project Description

`techdoc-summary` is a CLI tool that reads official technical documentation and release notes, then produces an operations-focused Markdown summary.

The long-term target sources are:

- Logstash
- Kafka
- Java
- Apache HTTP Server
- Tomcat
- Elasticsearch
- Kibana
- Kubernetes
- Docker

The MVP supports:

- Elasticsearch
- Kafka

The generated report should help an operator or developer quickly understand:

- current major/latest version information
- important changes
- breaking changes
- configuration notes and setting meanings
- bug fixes and improvements
- source links used to create the report

The first version should stay simple. It should not build a full RAG system, vector database, scheduled crawler, or web UI. The main goal is a reliable CLI structure that can be extended by adding source adapters.

## Project Structure

```text
techdoc-summary/
  README.md
  pyproject.toml
  reports/
  docs/
    superpowers/
      specs/
        2026-07-12-techdoc-summary-design.md
  src/
    techdoc_summary/
      __init__.py
      cli.py
      models.py
      fetcher.py
      summarizer.py
      renderer.py
      sources/
        __init__.py
        base.py
        elasticsearch.py
        kafka.py
  tests/
    test_cli.py
    test_renderer.py
    test_sources.py
```

### Main Components

`cli.py`
: Parses the source name, selects the matching adapter, runs the summary pipeline, and writes the report.

`models.py`
: Defines shared data models such as `SourceDocument`, `SummaryReport`, and `SummarySection`.

`sources/base.py`
: Defines the adapter interface. Every source adapter must implement the same contract.

`sources/elasticsearch.py`
: Knows which Elasticsearch official pages to read and how to convert them into common `SourceDocument` records.

`sources/kafka.py`
: Knows which Kafka official pages to read and how to convert them into common `SourceDocument` records.

`fetcher.py`
: Provides HTTP fetching and basic retry/error handling used by adapters.

`summarizer.py`
: Converts source documents into structured summary sections. The MVP can use rule-based extraction first, then later add OpenAI API summarization if needed.

`renderer.py`
: Converts a `SummaryReport` into English and Korean Markdown files and writes them under `reports/`.

## Data Flow

```text
CLI input
  -> source registry
  -> source adapter
  -> official docs/release notes
  -> SourceDocument list
  -> summarizer
  -> SummaryReport
  -> Markdown renderer
  -> reports/<source>-YYYY-MM-DD.en.md
  -> reports/<source>-YYYY-MM-DD.ko.md
```

Example output files:

```text
reports/elasticsearch-2026-07-12.en.md
reports/elasticsearch-2026-07-12.ko.md
reports/kafka-2026-07-12.en.md
reports/kafka-2026-07-12.ko.md
```

## Usage

### Recommended Development Setup

Use a virtual environment when developing or repeatedly running the project:

```bash
cd <project-root>
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Then run:

```bash
techdoc-summary elasticsearch
techdoc-summary kafka
```

Each command writes both English and Korean Markdown reports.

### Simple Module Execution

For a lightweight first run, the CLI should also support module execution:

```bash
cd <project-root>
python3 -m techdoc_summary.cli elasticsearch
python3 -m techdoc_summary.cli kafka
```

This path is useful before installing the package as a local CLI command.

### Expected Report Format

Each English report should use this shape:

```markdown
# Elasticsearch Summary

## Current Version

## Major Changes

## Breaking Changes

## Configuration Notes

## Bug Fixes

## Source Links
```

Each Korean report should use the same structure with Korean labels:

```markdown
# Elasticsearch 요약

## 현재 버전

## 주요 변경 사항

## 호환성 깨짐 변경 사항

## 설정 참고 사항

## 버그 수정

## 출처 링크
```

If a section cannot be confidently filled from the fetched official sources, the report should say that explicitly instead of inventing details.

## Adding A New Adapter

To add a new source such as Docker:

1. Create `src/techdoc_summary/sources/docker.py`.
2. Import `BaseSourceAdapter` and `SourceDocument`.
3. Implement `source_id`, `display_name`, and `fetch()`.
4. Register the adapter in `src/techdoc_summary/sources/__init__.py`.
5. Add tests for the adapter.
6. Run the CLI with the new source name.

Example:

```python
from techdoc_summary.models import SourceDocument
from techdoc_summary.sources.base import BaseSourceAdapter


class DockerAdapter(BaseSourceAdapter):
    source_id = "docker"
    display_name = "Docker"

    def fetch(self) -> list[SourceDocument]:
        return [
            SourceDocument(
                title="Docker release notes",
                url="https://docs.docker.com/release-notes/",
                content="Release note text fetched from the official Docker documentation.",
                section="release-notes",
            )
        ]
```

After registering the adapter, the CLI should work like this:

```bash
techdoc-summary docker
```

## Error Handling

The CLI should handle common failures clearly:

- unknown source name: show available source names
- network error: show the failing URL and retry status
- parsing failure: include the source URL and adapter name
- empty result: write a report section explaining that no usable content was found

The CLI should not silently produce a successful-looking report when source fetching or parsing failed.

## Testing

MVP tests should cover:

- CLI rejects unknown source names
- renderer writes the expected Markdown sections
- source registry returns Elasticsearch and Kafka adapters
- adapters return `SourceDocument` objects with title, URL, content, and section
- summary output includes source links

Network-dependent tests should use fixtures or mocked HTTP responses. Unit tests should not depend on live documentation sites.

## Implementation Scope

In scope for MVP:

- Python CLI project
- adapter-based source structure
- Elasticsearch adapter
- Kafka adapter
- Markdown report output
- tests for registry, renderer, and basic CLI behavior
- README with path, project description, structure, usage, and adapter instructions

Out of scope for MVP:

- web UI
- scheduler
- database
- vector search
- background crawling
- multi-user support
- automatic deployment

## Git

The project should not initialize git automatically. The user explicitly requested no git initialization. Superpowers design documentation is still kept under `docs/superpowers/specs/`.
