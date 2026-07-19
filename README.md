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
- Logstash

The long-term source list includes Java, Apache HTTP Server, Tomcat, Kibana, Kubernetes, and Docker.

Each report focuses on:

- current version information
- major changes
- breaking changes
- configuration notes
- bug fixes
- source links

Each CLI run writes both English and Korean reports:

```text
reports/<source>-YYYY-MM-DD.en.md
reports/<source>-YYYY-MM-DD.ko.md
```

## Project Structure

```text
techdoc-summary/
  README.md
  pyproject.toml
  reports/
  docs/
    superpowers/
      specs/
      plans/
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

## Usage

Recommended setup:

```bash
cd <project-root>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run installed CLI commands:

```bash
techdoc-summary all
techdoc-summary elasticsearch
techdoc-summary kafka
techdoc-summary logstash
```

Each command writes two files, one English report and one Korean report.
`all` runs every registered adapter.

Generate an automatic Kafka version impact report from official Kafka documents:

```bash
techdoc-summary kafka --from-version 3.7 --to-version 3.9 --output-dir reports
```

Generate an automatic Elasticsearch version impact report from official Elastic documents:

```bash
techdoc-summary elasticsearch --from-version 9.0 --to-version 9.2 --output-dir reports
```

Generate an automatic Logstash version impact report from official Elastic documents:

```bash
techdoc-summary logstash --from-version 7.17 --to-version 8.13 --output-dir reports
```

For version ranges, the tool fetches official release and upgrade documents,
extracts high-signal change sentences locally, and writes a report focused on:

- what changed
- operational impact
- actions to take
- configuration checklist
- source links

Run without installing the CLI command:

```bash
cd <project-root>
PYTHONPATH=src python3 -m techdoc_summary.cli all
PYTHONPATH=src python3 -m techdoc_summary.cli elasticsearch
PYTHONPATH=src python3 -m techdoc_summary.cli kafka
PYTHONPATH=src python3 -m techdoc_summary.cli logstash
PYTHONPATH=src python3 -m techdoc_summary.cli kafka --from-version 3.7 --to-version 3.9 --output-dir reports
PYTHONPATH=src python3 -m techdoc_summary.cli elasticsearch --from-version 9.0 --to-version 9.2 --output-dir reports
PYTHONPATH=src python3 -m techdoc_summary.cli logstash --from-version 7.17 --to-version 8.13 --output-dir reports
```

Write to a custom output directory:

```bash
techdoc-summary elasticsearch --output-dir reports
```

Run tests:

```bash
python3 -m pytest -v
```

If you want pytest installed inside the virtual environment too:

```bash
python -m pip install -e ".[dev]"
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
