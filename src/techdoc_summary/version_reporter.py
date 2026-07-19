from __future__ import annotations

import re
from datetime import date

from techdoc_summary.models import SourceDocument, SummaryReport, SummarySection


IMPORTANT_KEYWORDS = (
    "added",
    "new",
    "introduced",
    "preview",
    "early access",
    "deprecated",
    "removed",
    "migration",
    "upgrade",
    "compatibility",
    "configuration",
    "default",
    "security",
    "sasl",
    "ssl",
    "oauth",
    "java",
    "kraft",
    "zookeeper",
    "kip-",
)

CONFIG_KEYWORDS = (
    "configuration",
    "config",
    "property",
    "setting",
    "default",
    "sasl",
    "ssl",
    "oauth",
    "java",
    "tasks.max",
)

RISK_KEYWORDS = (
    "deprecated",
    "removed",
    "migration",
    "upgrade",
    "compatibility",
    "zookeeper",
    "kraft",
    "sasl",
    "oauth",
    "java",
)

NOISE_PHRASES = (
    "get started introduction quickstart",
    "get started free",
    "books and papers videos podcasts",
    "powered by apache",
    "apache software foundation",
    "all rights reserved",
    "trademarks",
    "loading elastic docs",
    "express our gratitude",
    "say thank you",
    "was the backbone",
    "hard work the community",
    "this release contains many",
    "we are proud",
    "we are excited",
    "see the upgrading to",
    "see the release notes for details",
    "to learn how to upgrade",
    "before you upgrade, carefully review",
    "review the deprecated functionality",
    "while deprecations have no immediate impact",
)


def generate_version_diff_report(
    source_id: str,
    display_name: str,
    from_version: str,
    to_version: str,
    documents: list[SourceDocument],
) -> SummaryReport:
    findings = _extract_findings(documents)
    range_label = f"{from_version} -> {to_version}"
    major_upgrade = _is_major_upgrade(from_version, to_version)

    return SummaryReport(
        source_id=source_id,
        display_name=display_name,
        generated_on=date.today(),
        sections=[
            _conclusion_section(display_name, from_version, to_version, findings, major_upgrade),
            _must_check_section(findings),
            _config_section(findings),
            _release_highlights_section(findings),
        ],
        source_links=_unique_links(documents),
        title_en=f"{display_name} {range_label} Upgrade Impact Report",
        title_ko=f"{display_name} {range_label} 업그레이드 영향 리포트",
        file_label=f"{source_id}-{from_version}-to-{to_version}",
    )


def _extract_findings(documents: list[SourceDocument]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen: set[str] = set()
    for document in documents:
        per_document_count = 0
        for sentence in _sentences(document.content):
            normalized = sentence.lower()
            if _is_noise(normalized):
                continue
            if not any(keyword in normalized for keyword in IMPORTANT_KEYWORDS):
                continue
            compact = _compact_sentence(sentence)
            if compact.lower() in seen:
                continue
            seen.add(compact.lower())
            findings.append(
                {
                    "title": _finding_title(compact),
                    "sentence": compact,
                    "source": document.title,
                    "url": document.url,
                }
            )
            per_document_count += 1
            if per_document_count >= 4:
                break
            if len(findings) >= 12:
                return findings
    return findings


def _is_noise(normalized_sentence: str) -> bool:
    return any(phrase in normalized_sentence for phrase in NOISE_PHRASES)


def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text)
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
        if len(item.strip()) >= 40
    ]


def _compact_sentence(sentence: str) -> str:
    sentence = sentence.strip()
    if len(sentence) <= 260:
        return sentence
    return sentence[:257].rstrip() + "..."


def _finding_title(sentence: str) -> str:
    lowered = sentence.lower()
    if "zookeeper" in lowered:
        return "ZooKeeper / KRaft"
    if "kraft" in lowered:
        return "KRaft"
    if "sasl" in lowered or "oauth" in lowered or "ssl" in lowered:
        return "Security/Auth"
    if "java" in lowered:
        return "Java Runtime"
    if "deprecated" in lowered:
        return "Deprecation"
    if "removed" in lowered:
        return "Removal"
    if "configuration" in lowered or "config" in lowered or "default" in lowered:
        return "Configuration"
    if "kip-" in lowered:
        match = re.search(r"KIP-\d+", sentence, flags=re.IGNORECASE)
        return match.group(0).upper() if match else "KIP"
    if "preview" in lowered or "early access" in lowered:
        return "Preview Feature"
    return "Release Change"


def _conclusion_section(
    display_name: str,
    from_version: str,
    to_version: str,
    findings: list[dict[str, str]],
    major_upgrade: bool,
) -> SummarySection:
    upgrade_type = "major" if major_upgrade else "minor"
    first = findings[0]["sentence"] if findings else "No high-signal change sentence was extracted."
    body = (
        f"- {display_name} {from_version} -> {to_version} is a {upgrade_type} version "
        f"upgrade. The most important extracted source signal is: {first}"
    )
    body_ko = (
        f"- {display_name} {from_version} -> {to_version} 업그레이드는 "
        f"{'major' if major_upgrade else 'minor'} 버전 변경입니다. 공식 문서에서 우선 확인된 핵심 문장은 다음입니다: {first}"
    )
    return SummarySection(title="Conclusion", body=body, body_ko=body_ko)


def _must_check_section(findings: list[dict[str, str]]) -> SummarySection:
    selected = _risk_findings(findings)[:6] or findings[:6]
    body_lines = [
        "| Item | Change | Impact | Action |",
        "|---|---|---|---|",
    ]
    body_ko_lines = [
        "| 항목 | 변경 내용 | 영향 | 해야 할 일 |",
        "|---|---|---|---|",
    ]
    for finding in selected:
        body_lines.append(
            f"| {finding['title']} | {finding['sentence']} | Review upgrade and compatibility impact. | Check the source note and validate in staging. |"
        )
        body_ko_lines.append(
            f"| {finding['title']} | {finding['sentence']} | 운영 호환성, 설정, 클라이언트 영향이 있을 수 있습니다. | 출처 문서를 확인하고 staging에서 검증합니다. |"
        )
    return SummarySection(
        title="Must Check",
        body="\n".join(body_lines),
        body_ko="\n".join(body_ko_lines),
    )


def _config_section(findings: list[dict[str, str]]) -> SummarySection:
    selected = [
        finding
        for finding in findings
        if any(keyword in finding["sentence"].lower() for keyword in CONFIG_KEYWORDS)
    ][:8]
    if not selected:
        selected = findings[:5]

    body = "\n".join(f"- {finding['sentence']}" for finding in selected)
    body_ko = "\n".join(
        f"- 공식 문서 확인 항목: {finding['sentence']}" for finding in selected
    )
    return SummarySection(
        title="Configuration Checklist",
        body=body or "- No configuration-specific sentence was extracted.",
        body_ko=body_ko or "- 설정 관련 핵심 문장을 추출하지 못했습니다.",
    )


def _release_highlights_section(findings: list[dict[str, str]]) -> SummarySection:
    selected = _balanced_findings(findings, limit=8)
    body = "\n".join(
        f"- {finding['source']}: {finding['sentence']}" for finding in selected
    )
    body_ko = "\n".join(
        f"- {finding['source']}: {finding['sentence']}" for finding in selected
    )
    return SummarySection(
        title="Release Highlights",
        body=body or "- No release highlight sentence was extracted.",
        body_ko=body_ko or "- 릴리즈 주요 문장을 추출하지 못했습니다.",
    )


def _balanced_findings(findings: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen_sources: set[str] = set()
    for finding in findings:
        if finding["source"] in seen_sources:
            continue
        selected.append(finding)
        seen_sources.add(finding["source"])
        if len(selected) >= limit:
            return selected

    for finding in findings:
        if finding in selected:
            continue
        selected.append(finding)
        if len(selected) >= limit:
            return selected
    return selected


def _risk_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        finding
        for finding in findings
        if any(keyword in finding["sentence"].lower() for keyword in RISK_KEYWORDS)
    ]


def _is_major_upgrade(from_version: str, to_version: str) -> bool:
    return from_version.split(".", maxsplit=1)[0] != to_version.split(".", maxsplit=1)[0]


def _unique_links(documents: list[SourceDocument]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for document in documents:
        if document.url not in seen:
            links.append(document.url)
            seen.add(document.url)
    return links
