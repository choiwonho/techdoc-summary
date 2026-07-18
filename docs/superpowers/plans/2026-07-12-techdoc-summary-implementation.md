# Techdoc Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that generates Markdown summaries for Elasticsearch and Kafka official documentation sources.

**Architecture:** The CLI selects a source adapter from a registry, adapters return common `SourceDocument` records, the summarizer converts records into a `SummaryReport`, and the renderer writes Markdown under `reports/`. The MVP uses deterministic, rule-based extraction so it can be tested without network or AI dependencies.

**Tech Stack:** Python 3.11+, standard library, `pytest` for tests, `ruff` optional for linting.

## Global Constraints

- Project path: `<project-root>`
- Do not initialize git automatically.
- Do not require live network access in unit tests.
- MVP source adapters: `elasticsearch`, `kafka`.
- Output format: Markdown files under `reports/<source>-YYYY-MM-DD.md`.
- If a section cannot be confidently filled, say so explicitly instead of inventing details.
- Keep the first version CLI-only. No web UI, scheduler, database, vector search, or deployment.
- README must include path, project description, project structure, usage, and adapter addition instructions.

---

## File Structure

Create these files:

```text
<project-root>/
  README.md
  pyproject.toml
  src/
    techdoc_summary/
      __init__.py
      cli.py
      models.py
      renderer.py
      summarizer.py
      sources/
        __init__.py
        base.py
        elasticsearch.py
        kafka.py
  tests/
    test_cli.py
    test_renderer.py
    test_sources.py
    test_summarizer.py
```

Responsibilities:

- `models.py`: dataclasses shared across adapters, summarizer, and renderer.
- `sources/base.py`: adapter abstract base class.
- `sources/elasticsearch.py`, `sources/kafka.py`: MVP adapters returning official source records.
- `sources/__init__.py`: source registry and lookup errors.
- `summarizer.py`: deterministic transformation from documents to report sections.
- `renderer.py`: Markdown formatting and report file writing.
- `cli.py`: argument parsing and pipeline orchestration.
- `README.md`: user-facing project guide.

---

### Task 1: Project Scaffold And Models

**Files:**
- Create: `<project-root>/pyproject.toml`
- Create: `<project-root>/src/techdoc_summary/__init__.py`
- Create: `<project-root>/src/techdoc_summary/models.py`
- Create: `<project-root>/tests/test_renderer.py`

**Interfaces:**
- Produces: `SourceDocument(title: str, url: str, content: str, section: str)`
- Produces: `SummarySection(title: str, body: str)`
- Produces: `SummaryReport(source_id: str, display_name: str, generated_on: date, sections: list[SummarySection], source_links: list[str])`

- [ ] **Step 1: Create package metadata**

Create `<project-root>/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "techdoc-summary"
version = "0.1.0"
description = "CLI summaries for official technical documentation and release notes."
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]

[project.scripts]
techdoc-summary = "techdoc_summary.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create package init**

Create `<project-root>/src/techdoc_summary/__init__.py`:

```python
"""Technical documentation summary CLI."""
```

- [ ] **Step 3: Write failing model import test**

Create `<project-root>/tests/test_renderer.py`:

```python
from datetime import date

from techdoc_summary.models import SummaryReport, SummarySection


def test_summary_report_model_can_be_created():
    report = SummaryReport(
        source_id="elasticsearch",
        display_name="Elasticsearch",
        generated_on=date(2026, 7, 12),
        sections=[SummarySection(title="Current Version", body="Version 9.x")],
        source_links=["https://www.elastic.co/docs"],
    )

    assert report.source_id == "elasticsearch"
    assert report.sections[0].title == "Current Version"
```

- [ ] **Step 4: Run test to verify it fails**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_renderer.py::test_summary_report_model_can_be_created -v
```

Expected: FAIL because `techdoc_summary.models` does not exist yet.

- [ ] **Step 5: Implement models**

Create `<project-root>/src/techdoc_summary/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceDocument:
    title: str
    url: str
    content: str
    section: str


@dataclass(frozen=True)
class SummarySection:
    title: str
    body: str


@dataclass(frozen=True)
class SummaryReport:
    source_id: str
    display_name: str
    generated_on: date
    sections: list[SummarySection]
    source_links: list[str]
```

- [ ] **Step 6: Run test to verify it passes**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_renderer.py::test_summary_report_model_can_be_created -v
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

Run:

```bash
find <project-root> -maxdepth 4 -type f | sort
```

Expected: `pyproject.toml`, `src/techdoc_summary/__init__.py`, `src/techdoc_summary/models.py`, and `tests/test_renderer.py` exist. Do not run `git init` or commit.

---

### Task 2: Markdown Renderer

**Files:**
- Create: `<project-root>/src/techdoc_summary/renderer.py`
- Modify: `<project-root>/tests/test_renderer.py`

**Interfaces:**
- Consumes: `SummaryReport`, `SummarySection`
- Produces: `render_markdown(report: SummaryReport) -> str`
- Produces: `write_report(report: SummaryReport, output_dir: Path) -> Path`

- [ ] **Step 1: Add failing renderer tests**

Append to `<project-root>/tests/test_renderer.py`:

```python
from pathlib import Path

from techdoc_summary.renderer import render_markdown, write_report


def test_render_markdown_includes_sections_and_source_links():
    report = SummaryReport(
        source_id="kafka",
        display_name="Kafka",
        generated_on=date(2026, 7, 12),
        sections=[
            SummarySection(title="Current Version", body="Kafka 4.x"),
            SummarySection(title="Bug Fixes", body="Several fixes are listed."),
        ],
        source_links=["https://kafka.apache.org/documentation/"],
    )

    markdown = render_markdown(report)

    assert markdown.startswith("# Kafka Summary")
    assert "## Current Version" in markdown
    assert "Kafka 4.x" in markdown
    assert "## Source Links" in markdown
    assert "- https://kafka.apache.org/documentation/" in markdown


def test_write_report_uses_source_and_date(tmp_path: Path):
    report = SummaryReport(
        source_id="elasticsearch",
        display_name="Elasticsearch",
        generated_on=date(2026, 7, 12),
        sections=[SummarySection(title="Major Changes", body="Important changes.")],
        source_links=["https://www.elastic.co/docs"],
    )

    path = write_report(report, tmp_path)

    assert path == tmp_path / "elasticsearch-2026-07-12.md"
    assert path.read_text(encoding="utf-8").startswith("# Elasticsearch Summary")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_renderer.py -v
```

Expected: FAIL because `techdoc_summary.renderer` does not exist yet.

- [ ] **Step 3: Implement renderer**

Create `<project-root>/src/techdoc_summary/renderer.py`:

```python
from __future__ import annotations

from pathlib import Path

from techdoc_summary.models import SummaryReport


def render_markdown(report: SummaryReport) -> str:
    lines = [
        f"# {report.display_name} Summary",
        "",
        f"Generated on: {report.generated_on.isoformat()}",
        "",
    ]

    for section in report.sections:
        lines.extend([f"## {section.title}", "", section.body.strip(), ""])

    lines.extend(["## Source Links", ""])
    if report.source_links:
        lines.extend(f"- {link}" for link in report.source_links)
    else:
        lines.append("No source links were collected.")

    lines.append("")
    return "\n".join(lines)


def write_report(report: SummaryReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report.source_id}-{report.generated_on.isoformat()}.md"
    path.write_text(render_markdown(report), encoding="utf-8")
    return path
```

- [ ] **Step 4: Run renderer tests**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_renderer.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_renderer.py -v
```

Expected: PASS. Do not run `git init` or commit.

---

### Task 3: Source Adapter Interface And Registry

**Files:**
- Create: `<project-root>/src/techdoc_summary/sources/base.py`
- Create: `<project-root>/src/techdoc_summary/sources/elasticsearch.py`
- Create: `<project-root>/src/techdoc_summary/sources/kafka.py`
- Create: `<project-root>/src/techdoc_summary/sources/__init__.py`
- Create: `<project-root>/tests/test_sources.py`

**Interfaces:**
- Consumes: `SourceDocument`
- Produces: `BaseSourceAdapter.fetch(self) -> list[SourceDocument]`
- Produces: `get_adapter(source_id: str) -> BaseSourceAdapter`
- Produces: `available_sources() -> list[str]`
- Produces: `UnknownSourceError(source_id: str, available: list[str])`

- [ ] **Step 1: Write failing source tests**

Create `<project-root>/tests/test_sources.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_sources.py -v
```

Expected: FAIL because `techdoc_summary.sources` does not exist yet.

- [ ] **Step 3: Implement base adapter**

Create `<project-root>/src/techdoc_summary/sources/base.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod

from techdoc_summary.models import SourceDocument


class BaseSourceAdapter(ABC):
    source_id: str
    display_name: str

    @abstractmethod
    def fetch(self) -> list[SourceDocument]:
        """Return official source documents converted into the common model."""
```

- [ ] **Step 4: Implement Elasticsearch adapter**

Create `<project-root>/src/techdoc_summary/sources/elasticsearch.py`:

```python
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
                content="Use the official Elasticsearch documentation to confirm the current release line and supported versions.",
            ),
            SourceDocument(
                title="Elasticsearch release notes",
                url="https://www.elastic.co/docs/release-notes/elasticsearch",
                section="release-notes",
                content="Review official Elasticsearch release notes for major changes, improvements, bug fixes, and known issues.",
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
                content="Use the configuration reference to understand Elasticsearch settings and operational impact.",
            ),
            SourceDocument(
                title="Elasticsearch bug fixes",
                url="https://www.elastic.co/docs/release-notes/elasticsearch",
                section="bug-fixes",
                content="Bug fixes are listed in the official Elasticsearch release notes.",
            ),
        ]
```

- [ ] **Step 5: Implement Kafka adapter**

Create `<project-root>/src/techdoc_summary/sources/kafka.py`:

```python
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
                content="Use the official Kafka documentation to confirm the current release line and configuration reference.",
            ),
            SourceDocument(
                title="Apache Kafka downloads",
                url="https://kafka.apache.org/downloads",
                section="release-notes",
                content="Use official Kafka downloads and release notes to review released versions and changes.",
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
                content="Use the Kafka configuration reference to understand broker, producer, consumer, and topic settings.",
            ),
            SourceDocument(
                title="Apache Kafka release notes",
                url="https://kafka.apache.org/downloads",
                section="bug-fixes",
                content="Bug fixes and improvements are linked from official Kafka release artifacts and notes.",
            ),
        ]
```

- [ ] **Step 6: Implement source registry**

Create `<project-root>/src/techdoc_summary/sources/__init__.py`:

```python
from __future__ import annotations

from techdoc_summary.sources.base import BaseSourceAdapter
from techdoc_summary.sources.elasticsearch import ElasticsearchAdapter
from techdoc_summary.sources.kafka import KafkaAdapter


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
}


def available_sources() -> list[str]:
    return sorted(_ADAPTERS)


def get_adapter(source_id: str) -> BaseSourceAdapter:
    try:
        adapter_class = _ADAPTERS[source_id]
    except KeyError as exc:
        raise UnknownSourceError(source_id, available_sources()) from exc
    return adapter_class()
```

- [ ] **Step 7: Run source tests**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_sources.py -v
```

Expected: PASS.

- [ ] **Step 8: Checkpoint**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_sources.py tests/test_renderer.py -v
```

Expected: PASS. Do not run `git init` or commit.

---

### Task 4: Rule-Based Summarizer

**Files:**
- Create: `<project-root>/src/techdoc_summary/summarizer.py`
- Create: `<project-root>/tests/test_summarizer.py`

**Interfaces:**
- Consumes: `SourceDocument`
- Produces: `summarize(source_id: str, display_name: str, documents: list[SourceDocument], generated_on: date | None = None) -> SummaryReport`

- [ ] **Step 1: Write failing summarizer tests**

Create `<project-root>/tests/test_summarizer.py`:

```python
from datetime import date

from techdoc_summary.models import SourceDocument
from techdoc_summary.summarizer import summarize


def test_summarizer_creates_standard_sections():
    documents = [
        SourceDocument(
            title="Current",
            url="https://example.com/current",
            section="current-version",
            content="Current release line is documented here.",
        ),
        SourceDocument(
            title="Config",
            url="https://example.com/config",
            section="configuration",
            content="Configuration settings are explained here.",
        ),
    ]

    report = summarize(
        source_id="example",
        display_name="Example",
        documents=documents,
        generated_on=date(2026, 7, 12),
    )

    assert [section.title for section in report.sections] == [
        "Current Version",
        "Major Changes",
        "Breaking Changes",
        "Configuration Notes",
        "Bug Fixes",
    ]
    assert report.source_links == ["https://example.com/current", "https://example.com/config"]


def test_summarizer_states_when_section_has_no_content():
    report = summarize(
        source_id="example",
        display_name="Example",
        documents=[],
        generated_on=date(2026, 7, 12),
    )

    assert "No official source content was collected" in report.sections[0].body
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_summarizer.py -v
```

Expected: FAIL because `techdoc_summary.summarizer` does not exist yet.

- [ ] **Step 3: Implement summarizer**

Create `<project-root>/src/techdoc_summary/summarizer.py`:

```python
from __future__ import annotations

from collections import defaultdict
from datetime import date

from techdoc_summary.models import SourceDocument, SummaryReport, SummarySection


SECTION_TITLES = {
    "current-version": "Current Version",
    "release-notes": "Major Changes",
    "breaking-changes": "Breaking Changes",
    "configuration": "Configuration Notes",
    "bug-fixes": "Bug Fixes",
}

SECTION_ORDER = [
    "current-version",
    "release-notes",
    "breaking-changes",
    "configuration",
    "bug-fixes",
]


def summarize(
    source_id: str,
    display_name: str,
    documents: list[SourceDocument],
    generated_on: date | None = None,
) -> SummaryReport:
    grouped: dict[str, list[SourceDocument]] = defaultdict(list)
    for document in documents:
        grouped[document.section].append(document)

    sections = [
        SummarySection(
            title=SECTION_TITLES[section_id],
            body=_section_body(section_id, grouped.get(section_id, [])),
        )
        for section_id in SECTION_ORDER
    ]

    return SummaryReport(
        source_id=source_id,
        display_name=display_name,
        generated_on=generated_on or date.today(),
        sections=sections,
        source_links=_unique_links(documents),
    )


def _section_body(section_id: str, documents: list[SourceDocument]) -> str:
    if not documents:
        title = SECTION_TITLES[section_id]
        return f"No official source content was collected for {title}."

    lines: list[str] = []
    for document in documents:
        lines.append(f"- {document.title}: {document.content} ({document.url})")
    return "\n".join(lines)


def _unique_links(documents: list[SourceDocument]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for document in documents:
        if document.url not in seen:
            links.append(document.url)
            seen.add(document.url)
    return links
```

- [ ] **Step 4: Run summarizer tests**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_summarizer.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_summarizer.py tests/test_sources.py tests/test_renderer.py -v
```

Expected: PASS. Do not run `git init` or commit.

---

### Task 5: CLI Pipeline

**Files:**
- Create: `<project-root>/src/techdoc_summary/cli.py`
- Create: `<project-root>/tests/test_cli.py`

**Interfaces:**
- Consumes: `get_adapter(source_id: str) -> BaseSourceAdapter`
- Consumes: `summarize(source_id: str, display_name: str, documents: list[SourceDocument], generated_on: date | None = None) -> SummaryReport`
- Consumes: `write_report(report: SummaryReport, output_dir: Path) -> Path`
- Produces: `run(source_id: str, output_dir: Path | None = None) -> Path`
- Produces: `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write failing CLI tests**

Create `<project-root>/tests/test_cli.py`:

```python
from pathlib import Path

from techdoc_summary.cli import main, run


def test_run_writes_report(tmp_path: Path):
    path = run("elasticsearch", output_dir=tmp_path)

    assert path == tmp_path / f"{path.stem}.md"
    assert path.name.startswith("elasticsearch-")
    assert "# Elasticsearch Summary" in path.read_text(encoding="utf-8")


def test_main_rejects_unknown_source(capsys):
    exit_code = main(["docker"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unknown source 'docker'" in captured.err
    assert "elasticsearch" in captured.err
    assert "kafka" in captured.err


def test_main_accepts_output_dir(tmp_path: Path, capsys):
    exit_code = main(["kafka", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote report:" in captured.out
    assert list(tmp_path.glob("kafka-*.md"))
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_cli.py -v
```

Expected: FAIL because `techdoc_summary.cli` does not exist yet.

- [ ] **Step 3: Implement CLI**

Create `<project-root>/src/techdoc_summary/cli.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from techdoc_summary.renderer import write_report
from techdoc_summary.sources import UnknownSourceError, available_sources, get_adapter
from techdoc_summary.summarizer import summarize


def run(source_id: str, output_dir: Path | None = None) -> Path:
    adapter = get_adapter(source_id)
    documents = adapter.fetch()
    report = summarize(
        source_id=adapter.source_id,
        display_name=adapter.display_name,
        documents=documents,
    )
    return write_report(report, output_dir or Path("reports"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techdoc-summary",
        description="Generate Markdown summaries for official technical documentation.",
    )
    parser.add_argument(
        "source",
        help=f"Source to summarize. Available: {', '.join(available_sources())}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory where the Markdown report will be written.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        path = run(args.source, args.output_dir)
    except UnknownSourceError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run:

```bash
cd <project-root>
python3 -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Manual CLI smoke test**

Run:

```bash
cd <project-root>
PYTHONPATH=src python3 -m techdoc_summary.cli elasticsearch --output-dir reports
PYTHONPATH=src python3 -m techdoc_summary.cli kafka --output-dir reports
```

Expected: two report paths printed, and files exist under `reports/`.

- [ ] **Step 7: Checkpoint**

Run:

```bash
cd <project-root>
find reports -maxdepth 1 -type f | sort
```

Expected: at least one `elasticsearch-YYYY-MM-DD.md` and one `kafka-YYYY-MM-DD.md`. Do not run `git init` or commit.

---

### Task 6: README And Adapter Instructions

**Files:**
- Create: `<project-root>/README.md`
- Modify: `<project-root>/tests/test_cli.py`

**Interfaces:**
- Consumes: CLI commands from Task 5.
- Produces: User-facing instructions for path, project description, structure, usage, and adapter additions.

- [ ] **Step 1: Add README content test**

Append to `<project-root>/tests/test_cli.py`:

```python
def test_readme_contains_required_user_sections():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Path" in readme
    assert "## Project Description" in readme
    assert "## Project Structure" in readme
    assert "## Usage" in readme
    assert "## Adding A New Adapter" in readme
```

- [ ] **Step 2: Run README test to verify failure**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_cli.py::test_readme_contains_required_user_sections -v
```

Expected: FAIL because `README.md` does not exist yet.

- [ ] **Step 3: Create README**

Create `<project-root>/README.md`:

```markdown
# Techdoc Summary

## Path

```markdown
<project-root>
```

## Project Description

`techdoc-summary` is a CLI tool that creates Markdown summaries from official technical documentation and release notes.

The MVP supports:

- Elasticsearch
- Kafka

The long-term source list includes Logstash, Java, Apache HTTP Server, Tomcat, Kibana, Kubernetes, and Docker.

Each report focuses on current version information, major changes, breaking changes, configuration notes, bug fixes, and source links.

## Project Structure

```text
techdoc-summary/
  README.md
  pyproject.toml
  reports/
  src/
    techdoc_summary/
      cli.py
      models.py
      renderer.py
      summarizer.py
      sources/
        base.py
        elasticsearch.py
        kafka.py
  tests/
```

## Usage

Recommended setup:

```bash
cd <project-root>
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run installed CLI commands:

```bash
techdoc-summary elasticsearch
techdoc-summary kafka
```

Run without installing the CLI command:

```bash
cd <project-root>
PYTHONPATH=src python3 -m techdoc_summary.cli elasticsearch
PYTHONPATH=src python3 -m techdoc_summary.cli kafka
```

Write to a custom output directory:

```bash
techdoc-summary elasticsearch --output-dir reports
```

## Adding A New Adapter

To add Docker:

1. Create `src/techdoc_summary/sources/docker.py`.
2. Implement a class that inherits `BaseSourceAdapter`.
3. Set `source_id = "docker"` and `display_name = "Docker"`.
4. Return `SourceDocument` records from `fetch()`.
5. Register the class in `src/techdoc_summary/sources/__init__.py`.
6. Add tests in `tests/test_sources.py`.
7. Run `techdoc-summary docker`.

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
```

- [ ] **Step 4: Run README test**

Run:

```bash
cd <project-root>
python3 -m pytest tests/test_cli.py::test_readme_contains_required_user_sections -v
```

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```bash
cd <project-root>
python3 -m pytest -v
PYTHONPATH=src python3 -m techdoc_summary.cli elasticsearch --output-dir reports
PYTHONPATH=src python3 -m techdoc_summary.cli kafka --output-dir reports
```

Expected: tests pass and both CLI commands write reports.

- [ ] **Step 6: Checkpoint**

Run:

```bash
cd <project-root>
find . -maxdepth 4 -type f | sort
```

Expected: README, pyproject, source files, tests, spec, plan, and generated reports are present. Do not run `git init` or commit.

---

## Final Verification

Run:

```bash
cd <project-root>
python3 -m pytest -v
PYTHONPATH=src python3 -m techdoc_summary.cli elasticsearch --output-dir reports
PYTHONPATH=src python3 -m techdoc_summary.cli kafka --output-dir reports
find reports -maxdepth 1 -type f | sort
```

Expected:

- all tests pass
- Elasticsearch report is generated
- Kafka report is generated
- no git repository is initialized unless the user separately asks for it

## Self-Review Notes

- Spec coverage: The plan covers CLI project setup, adapter structure, Elasticsearch and Kafka adapters, Markdown output, tests, README, usage instructions, and adapter addition instructions.
- Out-of-scope items remain excluded: web UI, scheduler, database, vector search, background crawling, multi-user support, and deployment.
- Type consistency: `SourceDocument`, `SummarySection`, `SummaryReport`, `BaseSourceAdapter.fetch`, `get_adapter`, `available_sources`, `summarize`, `render_markdown`, `write_report`, `run`, and `main` are consistently named across tasks.
- Git handling: The plan intentionally uses checkpoints instead of commits because the user requested no git initialization.
