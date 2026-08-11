# Report Schema v1

The normative machine-readable schema is [`schemas/tableproof-report-v1.schema.json`](../schemas/tableproof-report-v1.schema.json). TableProof v0.1 emits `schema_version: "1.0"`.

## Top level

- `tool`: tool name and semantic version.
- `audits`: one object per configured join, in configuration order.
- `summary`: audit, error, warning, and informational counts.
- `verdict`: `fail` when any error finding exists; otherwise `pass`.

No run timestamp is emitted. File hashes, input content, configuration, and tool version are sufficient to distinguish deterministic runs without making identical reports change on every invocation.

## Per-audit guarantees

Every audit contains:

- file path, SHA-256, delimiter, row/column counts, and key columns for both inputs;
- null-key and duplicate-key counts;
- expected and observed relationship;
- exact left/right unmatched distinct-key and row counts;
- inner/left/right/full row predictions and expansion factors;
- hypothetical whitespace, case, and leading-zero collision counts;
- severity-graded findings and verdict;
- optional result-file metadata, expected/actual rows, delta, and missing/excess key-multiset rows.

## Key examples

Default examples use `sha256:` followed by the first 16 hexadecimal characters of a SHA-256 digest. Composite components are joined with the ASCII unit separator before hashing. These examples are stable but are not an anonymization guarantee.

With explicit raw disclosure, composite examples are rendered with ` | ` between components.

## Stability policy

Additive fields may appear in a future compatible v1 minor release. Removing a field, changing its meaning/type, or changing key-hash construction requires a new major schema version. Consumers should check `schema_version` before processing.
