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
    assert report.source_links == [
        "https://example.com/current",
        "https://example.com/config",
    ]


def test_summarizer_states_when_section_has_no_content():
    report = summarize(
        source_id="example",
        display_name="Example",
        documents=[],
        generated_on=date(2026, 7, 12),
    )

    assert "No official source content was collected" in report.sections[0].body
