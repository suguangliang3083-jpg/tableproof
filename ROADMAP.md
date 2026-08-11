# Roadmap and evidence milestones

TableProof is useful only if it prevents real, reproducible join failures. Stars are a communication target, not a substitute for adoption or maintenance.

## Weeks 1–4: release v0.1.0

- Freeze v1 configuration and report semantics.
- Ship strict CSV/TSV parsing, key multiplicities, relationship checks, predictions, result multiset validation, CLI, Action, and Skill.
- Publish anonymized fixtures and a sub-two-minute demo using [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).
- Reserve repository and PyPI names only after live availability checks.
- Create signed `v0.1.0` and moving `v1` Git tags after CI passes.

## Weeks 5–6: independent trials

- Invite maintainers from at least three independent public bioinformatics, laboratory-data, or general CSV projects.
- Convert every reproducible report into a public issue or discussion and a minimal regression fixture with permission.
- Publish v0.1.x fixes; do not count private praise as public adoption.

## Weeks 7–8: evidence and v0.2

- Publish 2–3 consented case studies showing the declared contract, finding, correction, and rerun.
- Release v0.2.0 after at least two feedback-driven releases and five substantive public issues/discussions have been handled.
- Record 100 stars as an outreach target only. Never buy, exchange, automate, or misrepresent stars.
- Submit the Codex for Open Source application only with current, publicly verifiable evidence.

## Post-v0.2 candidates

- Bounded-memory/spill-to-disk key counting for very large files.
- Explicit schema mapping for result files with coalesced or renamed composite keys.
- Optional column-level provenance checks beyond the key multiset.
- SARIF output after a stable, reviewed mapping from findings to locations exists.
- Additional formats only after CSV/TSV behavior remains stable; XLSX and Parquet are out of v0.1 scope.

## Release gate

Every release requires green tests on Windows, Linux, and macOS; Python 3.11–3.14; a working example audit; reviewed schema changes; changelog notes; and no raw sensitive fixture data.
