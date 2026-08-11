# Contributing to TableProof

TableProof welcomes small, reproducible contributions that make join failures easier to detect without exposing research data.

## Before opening an issue

- Remove or replace sensitive values. Prefer a minimal synthetic fixture.
- State what one row represents in each table.
- State the ordered join keys and why they should be stable.
- State the expected relationship and join type.
- Include `tableproof --version`, platform, command, exit code, and the smallest privacy-safe report.

An adoption report must link to a public repository or other independently verifiable use. Private use is welcome but is not counted as public adoption evidence.

## Development setup

Python 3.11+ is sufficient; runtime dependencies are not allowed in v0.1.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m tableproof check --config examples/tableproof.toml
```

On PowerShell, set `$env:PYTHONPATH = "src"` before the commands.

## Pull requests

- Add a regression test for every behavior change or bug fix.
- Keep source files immutable in examples and tests; write repairs to new paths.
- Preserve exact-string key semantics and default hashing.
- Update the JSON schema and documentation when report fields change.
- Do not add telemetry, network calls, or runtime dependencies without a public design discussion.
- Add a changelog entry for user-visible changes.

By contributing, you agree that your contribution is licensed under the MIT License.
