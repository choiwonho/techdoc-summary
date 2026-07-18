# Kafka Version Diff Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Kafka version comparison report mode that explains major changes, upgrade cautions, configuration impact, and operational notes instead of producing a link-first report.

**Architecture:** Keep the existing adapter -> summarizer -> renderer flow. Add optional version-range inputs to the CLI and a Kafka adapter method that returns curated comparison `SourceDocument` records for `3.8 -> 4.1`.

**Tech Stack:** Python standard library, dataclasses, argparse, pytest.

## Global Constraints

- The first implementation targets Kafka only.
- No LLM or OpenAI API calls.
- Source links stay as supporting evidence at the end of the Markdown report.
- Existing generic Kafka reports must keep working when no version range is supplied.
- If only one of `--from-version` or `--to-version` is provided, the CLI exits with a clear message.

---

### Task 1: Kafka Comparison Documents

**Files:**
- Modify: `src/techdoc_summary/sources/kafka.py`
- Test: `tests/test_sources.py`

**Interfaces:**
- Consumes: existing `SourceDocument(title: str, url: str, content: str, section: str)`
- Produces: `KafkaAdapter.fetch_version_diff(from_version: str, to_version: str) -> list[SourceDocument]`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_sources.py`:

```python
def test_kafka_adapter_returns_version_diff_documents_for_3_8_to_4_1():
    adapter = KafkaAdapter()

    documents = adapter.fetch_version_diff("3.8", "4.1")

    assert len(documents) >= 5
    assert {document.section for document in documents} >= {
        "current-version",
        "release-notes",
        "breaking-changes",
        "configuration",
        "bug-fixes",
    }
    combined = "\n".join(document.content for document in documents)
    assert "Kafka 3.8에서 4.1" in combined
    assert "major-version upgrade" in combined
    assert "ZooKeeper" in combined
    assert "deprecated" in combined
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_sources.py::test_kafka_adapter_returns_version_diff_documents_for_3_8_to_4_1 -v`

Expected: FAIL with `AttributeError: 'KafkaAdapter' object has no attribute 'fetch_version_diff'`.

- [ ] **Step 3: Write minimal implementation**

Add this method to `KafkaAdapter` in `src/techdoc_summary/sources/kafka.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_sources.py::test_kafka_adapter_returns_version_diff_documents_for_3_8_to_4_1 -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/techdoc_summary/sources/kafka.py tests/test_sources.py
git commit -m "Add Kafka version diff source documents"
```

### Task 2: CLI Version Range Flow

**Files:**
- Modify: `src/techdoc_summary/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `KafkaAdapter.fetch_version_diff(from_version: str, to_version: str) -> list[SourceDocument]`
- Produces: CLI options `--from-version` and `--to-version` for `techdoc-summary kafka`

- [ ] **Step 1: Write the failing tests**

Add tests to `tests/test_cli.py` that verify:

```python
def test_kafka_command_accepts_version_range(tmp_path):
    exit_code = main([
        "kafka",
        "--from-version",
        "3.8",
        "--to-version",
        "4.1",
        "--output-dir",
        str(tmp_path),
    ])

    assert exit_code == 0
    korean_report = tmp_path / "kafka-2026-07-19.ko.md"
    assert korean_report.exists()
    markdown = korean_report.read_text(encoding="utf-8")
    assert "Kafka 3.8에서 4.1" in markdown
    assert "ZooKeeper" in markdown
    assert "deprecated" in markdown


def test_kafka_command_rejects_partial_version_range(tmp_path, capsys):
    exit_code = main([
        "kafka",
        "--from-version",
        "3.8",
        "--output-dir",
        str(tmp_path),
    ])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "from-version and to-version must be provided together" in captured.err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src python3 -m pytest tests/test_cli.py -v`

Expected: FAIL because the parser does not know the new options.

- [ ] **Step 3: Implement CLI flow**

In `src/techdoc_summary/cli.py`:

- Add `--from-version` and `--to-version` to the Kafka command parser.
- Validate that either both are present or neither is present.
- When both are present and the selected adapter has `fetch_version_diff`, call it instead of `fetch()`.
- Return exit code `2` with a clear stderr message for partial ranges.

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_sources.py tests/test_summarizer.py tests/test_renderer.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/techdoc_summary/cli.py tests/test_cli.py
git commit -m "Add Kafka version diff CLI mode"
```
