from __future__ import annotations

from pathlib import Path

from techdoc_summary.models import SummaryReport


SUPPORTED_LANGUAGES = ("en", "ko")

SECTION_TITLE_TRANSLATIONS = {
    "Current Version": "현재 버전",
    "Major Changes": "주요 변경 사항",
    "Breaking Changes": "호환성 깨짐 변경 사항",
    "Configuration Notes": "설정 참고 사항",
    "Bug Fixes": "버그 수정",
}

BODY_TRANSLATIONS = {
    "Elasticsearch documentation": "Elasticsearch 문서",
    "Elasticsearch release notes": "Elasticsearch 릴리스 노트",
    "Elasticsearch breaking changes": "Elasticsearch 호환성 깨짐 변경 사항",
    "Elasticsearch configuration": "Elasticsearch 설정",
    "Elasticsearch bug fixes": "Elasticsearch 버그 수정",
    "Apache Kafka documentation": "Apache Kafka 문서",
    "Apache Kafka downloads": "Apache Kafka 다운로드",
    "Apache Kafka upgrade notes": "Apache Kafka 업그레이드 노트",
    "Apache Kafka configuration": "Apache Kafka 설정",
    "Apache Kafka release notes": "Apache Kafka 릴리스 노트",
    "Use the official Elasticsearch documentation to confirm the current release line and supported versions.": (
        "공식 Elasticsearch 문서에서 현재 릴리스 라인과 지원 버전을 확인합니다."
    ),
    "Review official Elasticsearch release notes for major changes, improvements, bug fixes, and known issues.": (
        "공식 Elasticsearch 릴리스 노트에서 주요 변경 사항, 개선 사항, 버그 수정, 알려진 이슈를 확인합니다."
    ),
    "Review breaking changes before upgrading Elasticsearch clusters.": (
        "Elasticsearch 클러스터를 업그레이드하기 전에 호환성 깨짐 변경 사항을 확인합니다."
    ),
    "Use the configuration reference to understand Elasticsearch settings and operational impact.": (
        "설정 레퍼런스에서 Elasticsearch 설정과 운영 영향을 확인합니다."
    ),
    "Bug fixes are listed in the official Elasticsearch release notes.": (
        "버그 수정 내역은 공식 Elasticsearch 릴리스 노트에 정리되어 있습니다."
    ),
    "Use the official Kafka documentation to confirm the current release line and configuration reference.": (
        "공식 Kafka 문서에서 현재 릴리스 라인과 설정 레퍼런스를 확인합니다."
    ),
    "Use official Kafka downloads and release notes to review released versions and changes.": (
        "공식 Kafka 다운로드와 릴리스 노트에서 릴리스된 버전과 변경 사항을 확인합니다."
    ),
    "Review Kafka upgrade notes before changing broker or client versions.": (
        "브로커나 클라이언트 버전을 변경하기 전에 Kafka 업그레이드 노트를 확인합니다."
    ),
    "Use the Kafka configuration reference to understand broker, producer, consumer, and topic settings.": (
        "Kafka 설정 레퍼런스에서 브로커, 프로듀서, 컨슈머, 토픽 설정을 확인합니다."
    ),
    "Bug fixes and improvements are linked from official Kafka release artifacts and notes.": (
        "버그 수정과 개선 사항은 공식 Kafka 릴리스 산출물과 노트에 연결되어 있습니다."
    ),
    "No official source content was collected for Current Version.": (
        "현재 버전에 대해 수집된 공식 출처 내용이 없습니다."
    ),
    "No official source content was collected for Major Changes.": (
        "주요 변경 사항에 대해 수집된 공식 출처 내용이 없습니다."
    ),
    "No official source content was collected for Breaking Changes.": (
        "호환성 깨짐 변경 사항에 대해 수집된 공식 출처 내용이 없습니다."
    ),
    "No official source content was collected for Configuration Notes.": (
        "설정 참고 사항에 대해 수집된 공식 출처 내용이 없습니다."
    ),
    "No official source content was collected for Bug Fixes.": (
        "버그 수정에 대해 수집된 공식 출처 내용이 없습니다."
    ),
}


def render_markdown(report: SummaryReport, language: str = "en") -> str:
    _validate_language(language)
    title_suffix = "Summary" if language == "en" else "요약"
    generated_label = "Generated on" if language == "en" else "생성일"
    lines = [
        f"# {report.display_name} {title_suffix}",
        "",
        f"{generated_label}: {report.generated_on.isoformat()}",
        "",
    ]

    for section in report.sections:
        section_title = _translate_section_title(section.title, language)
        section_body = _translate_body(section.body.strip(), language)
        lines.extend([f"## {section_title}", "", section_body, ""])

    source_links_title = "Source Links" if language == "en" else "출처 링크"
    lines.extend([f"## {source_links_title}", ""])
    if report.source_links:
        lines.extend(f"- {link}" for link in report.source_links)
    else:
        no_links = (
            "No source links were collected."
            if language == "en"
            else "수집된 출처 링크가 없습니다."
        )
        lines.append(no_links)

    lines.append("")
    return "\n".join(lines)


def write_report(report: SummaryReport, output_dir: Path, language: str = "en") -> Path:
    _validate_language(language)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report.source_id}-{report.generated_on.isoformat()}.{language}.md"
    path.write_text(render_markdown(report, language=language), encoding="utf-8")
    return path


def write_reports(report: SummaryReport, output_dir: Path) -> list[Path]:
    return [write_report(report, output_dir, language=language) for language in SUPPORTED_LANGUAGES]


def _validate_language(language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )


def _translate_section_title(title: str, language: str) -> str:
    if language == "en":
        return title
    return SECTION_TITLE_TRANSLATIONS.get(title, title)


def _translate_body(body: str, language: str) -> str:
    if language == "en":
        return body

    translated = body
    for source, target in sorted(
        BODY_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        translated = translated.replace(source, target)
    return translated
