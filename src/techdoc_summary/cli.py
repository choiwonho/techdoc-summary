from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from techdoc_summary.renderer import write_reports
from techdoc_summary.sources import UnknownSourceError, available_sources, get_adapter
from techdoc_summary.sources.http import DocumentFetchError
from techdoc_summary.summarizer import summarize
from techdoc_summary.version_reporter import generate_version_diff_report


def run(source_id: str, output_dir: Optional[Path] = None) -> list[Path]:
    if source_id == "all":
        paths: list[Path] = []
        for available_source in available_sources():
            paths.extend(_run_one(available_source, output_dir))
        return paths

    return _run_one(source_id, output_dir)


def run_version_diff(
    source_id: str,
    from_version: str,
    to_version: str,
    output_dir: Optional[Path] = None,
) -> list[Path]:
    return _run_one(source_id, output_dir, from_version=from_version, to_version=to_version)


def _run_one(
    source_id: str,
    output_dir: Optional[Path] = None,
    from_version: Optional[str] = None,
    to_version: Optional[str] = None,
) -> list[Path]:
    adapter = get_adapter(source_id)
    if from_version and to_version and hasattr(adapter, "fetch_version_diff"):
        documents = adapter.fetch_version_diff(from_version, to_version)
        report = generate_version_diff_report(
            source_id=adapter.source_id,
            display_name=adapter.display_name,
            from_version=from_version,
            to_version=to_version,
            documents=documents,
        )
    else:
        documents = adapter.fetch()
        report = summarize(
            source_id=adapter.source_id,
            display_name=adapter.display_name,
            documents=documents,
        )
    return write_reports(report, output_dir or Path("reports"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techdoc-summary",
        description="Generate Markdown summaries for official technical documentation.",
    )
    parser.add_argument(
        "source",
        help=f"Source to summarize. Available: all, {', '.join(available_sources())}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory where the Markdown report will be written.",
    )
    parser.add_argument(
        "--from-version",
        help="Source version for a version comparison report.",
    )
    parser.add_argument(
        "--to-version",
        help="Target version for a version comparison report.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    try:
        if bool(args.from_version) != bool(args.to_version):
            print("from-version and to-version must be provided together", file=sys.stderr)
            return 2
        if args.from_version and args.to_version:
            paths = run_version_diff(
                args.source,
                args.from_version,
                args.to_version,
                args.output_dir,
            )
        else:
            paths = run(args.source, args.output_dir)
    except UnknownSourceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (DocumentFetchError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("Wrote reports:")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
