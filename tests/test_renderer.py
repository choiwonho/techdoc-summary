from datetime import date
from pathlib import Path

from techdoc_summary.models import SummaryReport, SummarySection
from techdoc_summary.renderer import render_markdown, write_report, write_reports


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


def test_render_markdown_supports_korean_output():
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

    markdown = render_markdown(report, language="ko")

    assert markdown.startswith("# Kafka 요약")
    assert "생성일: 2026-07-12" in markdown
    assert "## 현재 버전" in markdown
    assert "## 버그 수정" in markdown
    assert "## 출처 링크" in markdown


def test_render_markdown_translates_known_korean_body_without_partial_replacements():
    report = SummaryReport(
        source_id="elasticsearch",
        display_name="Elasticsearch",
        generated_on=date(2026, 7, 12),
        sections=[
            SummarySection(
                title="Current Version",
                body=(
                    "- Elasticsearch documentation: Use the official Elasticsearch "
                    "documentation to confirm the current release line and supported "
                    "versions. (https://www.elastic.co/docs)"
                ),
            ),
        ],
        source_links=["https://www.elastic.co/docs"],
    )

    markdown = render_markdown(report, language="ko")

    assert "공식 Elasticsearch 문서에서 현재 릴리스 라인과 지원 버전을 확인합니다." in markdown
    assert "Use the official" not in markdown


def test_write_report_uses_source_date_and_language(tmp_path: Path):
    report = SummaryReport(
        source_id="elasticsearch",
        display_name="Elasticsearch",
        generated_on=date(2026, 7, 12),
        sections=[SummarySection(title="Major Changes", body="Important changes.")],
        source_links=["https://www.elastic.co/docs"],
    )

    path = write_report(report, tmp_path, language="en")

    assert path == tmp_path / "elasticsearch-2026-07-12.en.md"
    assert path.read_text(encoding="utf-8").startswith("# Elasticsearch Summary")


def test_write_reports_creates_english_and_korean_files(tmp_path: Path):
    report = SummaryReport(
        source_id="elasticsearch",
        display_name="Elasticsearch",
        generated_on=date(2026, 7, 12),
        sections=[SummarySection(title="Configuration Notes", body="Settings are listed.")],
        source_links=["https://www.elastic.co/docs"],
    )

    paths = write_reports(report, tmp_path)

    assert paths == [
        tmp_path / "elasticsearch-2026-07-12.en.md",
        tmp_path / "elasticsearch-2026-07-12.ko.md",
    ]
    assert "# Elasticsearch Summary" in paths[0].read_text(encoding="utf-8")
    assert "# Elasticsearch 요약" in paths[1].read_text(encoding="utf-8")
