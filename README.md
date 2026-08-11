# TableProof

**Prove that a CSV/TSV join preserves the records you think it does.**

TableProof is a zero-runtime-dependency Python CLI, GitHub Action, and Agent Skill for auditing tabular joins before they silently drop, duplicate, or mis-associate research records. It checks exact key multiplicities, declared cardinality, blank keys, orphans, predicted output sizes, normalization hazards, and—when supplied—the exact key multiset of a materialized result.

[中文指南](README.zh-CN.md) · [Configuration](docs/CONFIGURATION.md) · [Report Schema v1](docs/REPORT_SCHEMA.md) · [Roadmap](ROADMAP.md)

> Status: v0.1.0 was published on GitHub and PyPI on 2026-08-11 after the full CI matrix passed. No independent adoption, download, star, or program-acceptance claims are made here.

## Why this exists

A join can finish without errors while producing scientifically wrong data:

- a supposedly unique sample key repeats and multiplies measurements;
- an inner join silently removes subjects missing from one table;
- identifiers such as `001` and `1` fail to match after a spreadsheet changed types;
- two different missing and excess records cancel out, leaving the expected row count;
- a many-to-many join expands thousands of rows from a small duplicated key group.

TableProof turns the intended join into an explicit, reviewable contract. Its verdict is deterministic and does not use an LLM or the OpenAI API.

## Install

TableProof requires Python 3.11 or later and has no runtime dependencies.

From a source checkout:

```bash
python -m pip install .
tableproof --version
```

Install the published package from PyPI:

```bash
python -m pip install tableproof
```

## Two-minute start

Create an annotated configuration:

```bash
tableproof init
```

Audit every declared join:

```bash
tableproof check --config tableproof.toml
```

Run a one-off check:

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many
```

Verify an existing result and write a machine-readable report:

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many \
  --result merged.tsv --join-type left \
  --format json --output tableproof-report.json
```

The repository example is executable without installing:

```bash
PYTHONPATH=src python -m tableproof check --config examples/tableproof.toml
```

On PowerShell, set `$env:PYTHONPATH = "src"` first.

## Join contract

```toml
version = 1

[report]
show_raw_keys = false
sample_limit = 5
fail_on = "error"

[[joins]]
name = "samples-to-results"
left = "data/samples.tsv"
right = "data/results.tsv"
left_keys = ["sample_id"]
right_keys = ["sample_id"]
relationship = "one-to-many"
left_unmatched = "error"
right_unmatched = "warn"
null_keys = "error"
result = "data/merged.tsv" # optional
join_type = "left"         # required with result
```

`one-to-many` is a constraint: the left must be unique and the right may repeat. A currently 1:1 dataset is a valid, narrower observation. `many-to-many` allows repetition on both sides but always produces an expansion warning.

Composite keys use ordered arrays. Repeat `--left-key`/`--right-key` in direct mode or provide comma-separated names. If a result uses a different key name, add `result_keys` or `--result-key`.

## What TableProof checks

- UTF-8/UTF-8 BOM decoding, CSV/TSV delimiter, header validity, repeated headers, and row width.
- Missing, blank, single-column, and composite keys.
- Duplicate key groups and excess duplicate rows on each side.
- Observed 1:1, 1:N, N:1, or N:N multiplicity against the declared constraint.
- Left and right orphan keys and rows.
- Exact predicted rows and expansion factors for inner, left, right, and full joins.
- Potential cross-table collisions after hypothetical trimming, case-folding, or leading-zero removal.
- Exact expected-versus-actual result key multisets, not only row counts.
- SHA-256 of every input/result file for provenance.

Keys are always original strings. TableProof never trims, case-folds, parses numbers, removes leading zeros, deduplicates, or rewrites source data. A normalization collision is a warning to investigate—not permission to merge identifiers.

## Output and exit codes

Use `--format text|json|markdown` and `--output PATH`. JSON uses the stable [Report Schema v1](schemas/tableproof-report-v1.schema.json) and contains no run timestamp, so identical files and settings produce identical content.

- `0`: configured threshold passed.
- `1`: data violated a policy, or warnings exist with `--fail-on warning`.
- `2`: configuration, CLI, encoding, parsing, I/O, or result-key inference error.

By default, reports expose counts and truncated SHA-256 key examples. `--show-raw-keys` or `[report].show_raw_keys = true` is an explicit disclosure choice and should be reviewed before use in public CI.

## GitHub Action

After publishing the repository and a maintained `v1` tag:

```yaml
name: TableProof
on: [push, pull_request]

permissions:
  contents: read

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: suguangliang3083-jpg/tableproof@v1
        with:
          config: tableproof.toml
          fail-on: error
          report-dir: tableproof-reports
```

The Action requires no API key and no write permission. It creates error/warning annotations, appends a job summary, and exposes JSON/Markdown report paths. It always forces hashed examples—even if a pull request changes `show_raw_keys`—and confines all paths to `GITHUB_WORKSPACE`. Uploading report files as an artifact remains an explicit workflow choice.

## Agent Skill

The open Agent Skills-compatible workflow lives at [`.agents/skills/table-proof`](.agents/skills/table-proof/SKILL.md). It requires an agent to establish what each row represents, confirm key stability and the expected relationship, invoke the deterministic CLI, and keep repair advice separate from source-data modification.

Copy that directory into a project's `.agents/skills/` folder, or keep it in a repository that Codex opens. The Skill does not silently install TableProof.

## Scope and limitations

- v0.1 supports CSV and TSV only, encoded as UTF-8 or UTF-8 with BOM.
- Tables are held as key-frequency maps in memory. Very high-cardinality inputs can require substantial RAM; streaming/spill-to-disk support is a roadmap item.
- Blank key components never match, including another blank key, consistent with SQL null-key behavior.
- Result validation compares the declared join-key multiset. It does not prove that every non-key value came from the correct source row.
- Hash examples are privacy-reducing identifiers, not anonymization guarantees; low-entropy keys can be guessed.

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m tableproof check --config examples/tableproof.toml
```

The CI matrix covers Windows, Linux, macOS, and Python 3.11–3.14. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Open-source program context

TableProof should earn adoption by preventing real data-integrity failures, not exist as an application shell. The repository includes an [evidence ledger and draft](docs/CODEX_FOR_OSS_APPLICATION.md) that forbids invented metrics. OpenAI's program is selective and rolling; building this repository does not guarantee acceptance or benefits. Recheck the current [Codex for Open Source page](https://developers.openai.com/community/codex-for-oss) and [program terms](https://learn.chatgpt.com/docs/codex-for-oss-terms) before applying. The Skill structure follows the current [Build Skills guide](https://learn.chatgpt.com/docs/build-skills).

## License

MIT
