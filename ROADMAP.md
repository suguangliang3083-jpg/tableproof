# Roadmap

The roadmap follows reported use rather than a fixed calendar. Open an issue or discussion with a synthetic reproducer when possible.

## Released

### v0.1.0 — 2026-08-11

- CSV/TSV parsing and exact-string single or composite keys;
- blank, duplicate, cardinality, and unmatched-key checks;
- predicted rows for inner, left, right, and full joins;
- result key-multiset validation;
- text, JSON, and Markdown reports;
- Python CLI, GitHub Action, and Agent Skill.

## v0.1.x maintenance

- Correct documented or reproducible defects without changing report semantics unnecessarily.
- Keep the CLI dependency-free and preserve exit-code behavior.
- Update CI action runtimes as GitHub retires older Node.js versions.
- Improve installation and examples when users report unclear steps.

## v0.2 gate

Plan v0.2 after at least three independent public uses are documented and enough feedback exists to justify interface changes. Candidate work must be tied to an issue, discussion, or case study. Likely areas include:

- bounded-memory or spill-to-disk key counting;
- clearer result-key mapping for renamed or coalesced composite keys;
- optional checks for selected non-key provenance;
- SARIF output with a reviewed finding-to-location mapping.

XLSX, Parquet, and a hosted service are not planned for v0.1.x.

## Release checks

Every release requires:

- tests on Windows, Linux, and macOS with Python 3.11–3.14;
- a passing example audit;
- schema review for report changes;
- changelog notes;
- inspection of fixtures for sensitive data;
- verification of the GitHub Action and Agent Skill instructions.

Adoption and maintenance evidence is recorded in [`docs/CODEX_FOR_OSS_APPLICATION.md`](docs/CODEX_FOR_OSS_APPLICATION.md). Stars are not treated as proof that the tool is in use.
