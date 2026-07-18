from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from techdoc_summary.renderer import write_reports
from techdoc_summary.sources import UnknownSourceError, available_sources, get_adapter
from techdoc_summary.summarizer import summarize


def run(source_id: str, output_dir: Optional[Path] = None) -> list[Path]:
    if source_id == "all":
        paths: list[Path] = []
        for available_source in available_sources():
            paths.extend(_run_one(available_source, output_dir))
        return paths

    return _run_one(source_id, output_dir)


def _run_one(source_id: str, output_dir: Optional[Path] = None) -> list[Path]:
    adapter = get_adapter(source_id)
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
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    try:
        paths = run(args.source, args.output_dir)
    except UnknownSourceError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("Wrote reports:")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
