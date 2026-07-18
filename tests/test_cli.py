from pathlib import Path

from techdoc_summary.cli import main, run


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
    assert len(names) == 4
    assert names[0].startswith("elasticsearch-")
    assert names[0].endswith(".en.md")
    assert names[1].startswith("elasticsearch-")
    assert names[1].endswith(".ko.md")
    assert names[2].startswith("kafka-")
    assert names[2].endswith(".en.md")
    assert names[3].startswith("kafka-")
    assert names[3].endswith(".ko.md")


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
    assert list(tmp_path.glob("elasticsearch-*.en.md"))
    assert list(tmp_path.glob("elasticsearch-*.ko.md"))
    assert list(tmp_path.glob("kafka-*.en.md"))
    assert list(tmp_path.glob("kafka-*.ko.md"))


def test_kafka_command_accepts_version_range(tmp_path: Path, capsys):
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
    korean_reports = list(tmp_path.glob("kafka-*.ko.md"))
    assert len(korean_reports) == 1
    markdown = korean_reports[0].read_text(encoding="utf-8")
    assert "Kafka 3.8에서 4.1" in markdown
    assert "ZooKeeper" in markdown
    assert "deprecated" in markdown


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
