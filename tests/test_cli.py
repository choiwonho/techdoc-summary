from pathlib import Path

from techdoc_summary.cli import main, run
from techdoc_summary.models import SourceDocument, SummaryReport, SummarySection


class FakeVersionAdapter:
    def __init__(self, source_id: str, display_name: str) -> None:
        self.source_id = source_id
        self.display_name = display_name

    def fetch_version_diff(self, from_version: str, to_version: str) -> list[SourceDocument]:
        return [
            SourceDocument(
                title=f"{self.display_name} {from_version} to {to_version}",
                url=f"https://example.com/{self.source_id}/upgrade",
                section="source-material",
                content=(
                    f"Official {self.display_name} source material for "
                    f"{from_version} -> {to_version}"
                ),
            )
        ]


def install_fake_version_report(
    monkeypatch, expected_source_id: str = "kafka", display_name: str = "Kafka"
):
    def fake_get_adapter(source_id: str):
        assert source_id == expected_source_id
        return FakeVersionAdapter(expected_source_id, display_name)

    def fake_generate_version_diff_report(
        source_id: str,
        display_name: str,
        from_version: str,
        to_version: str,
        documents: list[SourceDocument],
    ) -> SummaryReport:
        assert documents[0].section == "source-material"
        return SummaryReport(
            source_id=source_id,
            display_name=display_name,
            generated_on=__import__("datetime").date(2026, 7, 19),
            sections=[
                SummarySection(
                    title="Conclusion",
                    body=f"- {display_name} {from_version}에서 {to_version} 자동 분석 결과입니다.",
                ),
                SummarySection(
                    title="Must Check",
                    body=(
                        "| 항목 | 변경 내용 | 영향 | 해야 할 일 |\n"
                        "|---|---|---|---|\n"
                        "| KRaft 전환 | ZooKeeper 관련 변경 | 운영 영향 | migration 확인 |\n"
                        "| ZooKeeper 종료 준비 | 3.x 라인의 마지막 major release | 4.0 준비 필요 | Dynamic KRaft Quorum과 tasks.max 확인 |\n"
                    ),
                ),
                SummarySection(
                    title="Configuration Checklist",
                    body="- OAuthBearer 확인\n- tasks.max 확인",
                ),
                SummarySection(
                    title="Release Highlights",
                    body="- Dynamic KRaft Quorum\n- 3.x 라인의 마지막 major release",
                ),
            ],
            source_links=[documents[0].url],
            title_en=f"{display_name} {from_version} -> {to_version} Upgrade Impact Report",
            title_ko=f"{display_name} {from_version} -> {to_version} 업그레이드 영향 리포트",
            file_label=f"{expected_source_id}-{from_version}-to-{to_version}",
        )

    monkeypatch.setattr("techdoc_summary.cli.get_adapter", fake_get_adapter)
    monkeypatch.setattr(
        "techdoc_summary.cli.generate_version_diff_report",
        fake_generate_version_diff_report,
    )


def test_run_writes_report(tmp_path: Path):
    paths = run("elasticsearch", output_dir=tmp_path)

    assert len(paths) == 2
    assert paths[0].name.startswith("elasticsearch-")
    assert paths[0].name.endswith(".en.md")
    assert paths[1].name.endswith(".ko.md")
    assert "# Elasticsearch Summary" in paths[0].read_text(encoding="utf-8")
    assert "# Elasticsearch 요약" in paths[1].read_text(encoding="utf-8")


def test_run_all_writes_reports_for_every_registered_source(tmp_path: Path):
    paths = run("all", output_dir=tmp_path)

    names = [path.name for path in paths]
    assert len(names) == 6
    assert names[0].startswith("elasticsearch-")
    assert names[0].endswith(".en.md")
    assert names[1].startswith("elasticsearch-")
    assert names[1].endswith(".ko.md")
    assert names[2].startswith("kafka-")
    assert names[2].endswith(".en.md")
    assert names[3].startswith("kafka-")
    assert names[3].endswith(".ko.md")
    assert names[4].startswith("logstash-")
    assert names[4].endswith(".en.md")
    assert names[5].startswith("logstash-")
    assert names[5].endswith(".ko.md")


def test_main_rejects_unknown_source(capsys):
    exit_code = main(["docker"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unknown source 'docker'" in captured.err
    assert "elasticsearch" in captured.err
    assert "kafka" in captured.err
    assert "logstash" in captured.err


def test_main_accepts_output_dir(tmp_path: Path, capsys):
    exit_code = main(["kafka", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote reports:" in captured.out
    assert list(tmp_path.glob("kafka-*.en.md"))
    assert list(tmp_path.glob("kafka-*.ko.md"))


def test_main_accepts_all_source(tmp_path: Path, capsys):
    exit_code = main(["all", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote reports:" in captured.out
    assert "elasticsearch-" in captured.out
    assert "kafka-" in captured.out
    assert "logstash-" in captured.out
    assert list(tmp_path.glob("elasticsearch-*.en.md"))
    assert list(tmp_path.glob("elasticsearch-*.ko.md"))
    assert list(tmp_path.glob("kafka-*.en.md"))
    assert list(tmp_path.glob("kafka-*.ko.md"))
    assert list(tmp_path.glob("logstash-*.en.md"))
    assert list(tmp_path.glob("logstash-*.ko.md"))


def test_kafka_command_accepts_version_range(tmp_path: Path, capsys, monkeypatch):
    install_fake_version_report(monkeypatch)
    exit_code = main(
        [
            "kafka",
            "--from-version",
            "3.8",
            "--to-version",
            "4.1",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote reports:" in captured.out
    korean_reports = list(tmp_path.glob("kafka-3.8-to-4.1-*.ko.md"))
    assert len(korean_reports) == 1
    markdown = korean_reports[0].read_text(encoding="utf-8")
    assert markdown.startswith("# Kafka 3.8 -> 4.1 업그레이드 영향 리포트")
    assert "## 결론" in markdown
    assert "## 반드시 확인할 것" in markdown
    assert "| 항목 | 변경 내용 | 영향 | 해야 할 일 |" in markdown
    assert "| KRaft 전환 |" in markdown
    assert "## 설정 변경 체크리스트" in markdown
    assert "Kafka 3.8에서 4.1" in markdown
    assert "ZooKeeper" in markdown
    assert "OAuthBearer" in markdown


def test_kafka_version_range_report_does_not_overwrite_generic_report(
    tmp_path: Path, monkeypatch
):
    generic_paths = run("kafka", output_dir=tmp_path)
    install_fake_version_report(monkeypatch)
    exit_code = main(
        [
            "kafka",
            "--from-version",
            "3.8",
            "--to-version",
            "4.1",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert {path.name for path in generic_paths} == {
        "kafka-2026-07-19.en.md",
        "kafka-2026-07-19.ko.md",
    }
    assert (tmp_path / "kafka-2026-07-19.ko.md").exists()
    assert (tmp_path / "kafka-3.8-to-4.1-2026-07-19.ko.md").exists()
    generic_markdown = (tmp_path / "kafka-2026-07-19.ko.md").read_text(encoding="utf-8")
    diff_markdown = (tmp_path / "kafka-3.8-to-4.1-2026-07-19.ko.md").read_text(
        encoding="utf-8"
    )
    assert generic_markdown.startswith("# Kafka 요약")
    assert diff_markdown.startswith("# Kafka 3.8 -> 4.1 업그레이드 영향 리포트")


def test_kafka_command_accepts_3_7_to_3_9_version_range(tmp_path: Path, capsys, monkeypatch):
    install_fake_version_report(monkeypatch)
    exit_code = main(
        [
            "kafka",
            "--from-version",
            "3.7",
            "--to-version",
            "3.9",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote reports:" in captured.out
    korean_report = tmp_path / "kafka-3.7-to-3.9-2026-07-19.ko.md"
    assert korean_report.exists()
    markdown = korean_report.read_text(encoding="utf-8")
    assert markdown.startswith("# Kafka 3.7 -> 3.9 업그레이드 영향 리포트")
    assert "| ZooKeeper 종료 준비 |" in markdown
    assert "3.x 라인의 마지막 major release" in markdown
    assert "Dynamic KRaft Quorum" in markdown
    assert "tasks.max" in markdown


def test_elasticsearch_command_accepts_version_range(tmp_path: Path, capsys, monkeypatch):
    install_fake_version_report(
        monkeypatch,
        expected_source_id="elasticsearch",
        display_name="Elasticsearch",
    )
    exit_code = main(
        [
            "elasticsearch",
            "--from-version",
            "9.0",
            "--to-version",
            "9.2",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote reports:" in captured.out
    korean_report = tmp_path / "elasticsearch-9.0-to-9.2-2026-07-19.ko.md"
    assert korean_report.exists()
    markdown = korean_report.read_text(encoding="utf-8")
    assert markdown.startswith("# Elasticsearch 9.0 -> 9.2 업그레이드 영향 리포트")
    assert "## 결론" in markdown
    assert "## 반드시 확인할 것" in markdown
    assert "| 항목 | 변경 내용 | 영향 | 해야 할 일 |" in markdown


def test_logstash_command_accepts_version_range(tmp_path: Path, capsys, monkeypatch):
    install_fake_version_report(
        monkeypatch,
        expected_source_id="logstash",
        display_name="Logstash",
    )
    exit_code = main(
        [
            "logstash",
            "--from-version",
            "7.17",
            "--to-version",
            "8.13",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Wrote reports:" in captured.out
    korean_report = tmp_path / "logstash-7.17-to-8.13-2026-07-19.ko.md"
    assert korean_report.exists()
    markdown = korean_report.read_text(encoding="utf-8")
    assert markdown.startswith("# Logstash 7.17 -> 8.13 업그레이드 영향 리포트")
    assert "## 결론" in markdown
    assert "## 반드시 확인할 것" in markdown


def test_kafka_command_rejects_partial_version_range(tmp_path: Path, capsys):
    exit_code = main(
        [
            "kafka",
            "--from-version",
            "3.8",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "from-version and to-version must be provided together" in captured.err


def test_help_mentions_all_source(capsys):
    exit_code = main(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "all" in captured.out


def test_readme_contains_required_user_sections():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Path" in readme
    assert "## Project Description" in readme
    assert "## Project Structure" in readme
    assert "## Usage" in readme
    assert "## Adding A New Adapter" in readme
