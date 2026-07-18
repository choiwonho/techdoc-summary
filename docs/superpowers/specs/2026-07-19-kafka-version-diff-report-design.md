# Kafka Version Diff Report Design

## Goal

`techdoc-summary` should produce an actionable Kafka version comparison report, not a link-first document index. For a range such as `3.8 -> 4.1`, the report should explain the major changes, upgrade cautions, configuration impact, and operational notes in readable prose. Source links remain useful, but they are supporting evidence rather than the main output.

## Scope

The first implementation targets Kafka only.

It adds CLI support for:

```bash
techdoc-summary kafka --from-version 3.8 --to-version 4.1
```

The output remains Markdown and still writes English and Korean reports through the existing renderer path. The source links section stays at the end.

## Data Flow

1. `KafkaAdapter.fetch()` continues to provide official Kafka source documents.
2. When both `--from-version` and `--to-version` are provided, the CLI asks the adapter for version comparison documents instead of generic source documents.
3. The Kafka adapter returns structured `SourceDocument` records whose `content` fields contain concise, human-readable findings.
4. The existing summarizer groups those findings into standard report sections.
5. The renderer writes a report where links are secondary.

## Report Sections

The Kafka comparison report should use the existing section model:

- `Current Version`: comparison range and overall upgrade posture.
- `Major Changes`: important platform, runtime, protocol, or feature changes.
- `Breaking Changes`: upgrade blockers, removed behavior, compatibility issues, or migration requirements.
- `Configuration Notes`: settings and defaults that operators should review.
- `Bug Fixes`: important fixes and improvements included in the target range.

For Korean output, the body should be readable Korean rather than a mechanical link translation.

## Kafka Rule-Based Extraction

This implementation is intentionally rule-based and offline-friendly. It does not call an LLM.

For the initial Kafka range report, the adapter will include curated rules for known Kafka version ranges and broad upgrade topics. The rules should be explicit, testable, and easy to replace later with a real official-document parser.

The first useful range is `3.8 -> 4.1`. It should highlight:

- Kafka 4.x is a major-version upgrade, so users should treat it as an upgrade project rather than a patch update.
- ZooKeeper-era assumptions and legacy compatibility paths require extra review when moving into the 4.x line.
- Broker, client, Kafka Streams, Connect, and tooling compatibility should be checked before rollout.
- Deprecated or removed settings and changed defaults should be reviewed against production configs.
- The generated report should point readers to official upgrade and release-note pages only after explaining the practical impact.

## Error Handling

- If only one of `--from-version` or `--to-version` is provided, the CLI should exit with a clear message.
- If a comparison range has no curated rule coverage, the report should still be generated with a clear "no curated findings" message and official source links.
- Existing generic Kafka reports should keep working when no version range is supplied.

## Testing

Add focused tests for:

- CLI config accepting `--from-version` and `--to-version`.
- Kafka adapter returning comparison documents for `3.8 -> 4.1`.
- Summary output containing major changes and upgrade cautions, not just links.
- Existing generic report behavior remaining intact.
