# TableProof

TableProof checks whether a CSV or TSV join behaves as intended.

Given two tables and a join contract, it reports blank and duplicate keys, observed cardinality, unmatched records, predicted output rows, possible normalization collisions, and—when provided—differences in an existing result table. The command-line tool uses only the Python standard library. Agent integrations call the same CLI and do not decide the verdict themselves.

[中文说明](README.zh-CN.md) · [Configuration](docs/CONFIGURATION.md) · [Report schema](docs/REPORT_SCHEMA.md) · [Agent Skill setup](docs/AGENT_SKILL.md) · [Roadmap](ROADMAP.md)

Latest release: [`v0.1.1`](https://github.com/suguangliang3083-jpg/tableproof/releases/tag/v0.1.1), also available on [PyPI](https://pypi.org/project/tableproof/).

## The problem

A join can run successfully and still change the dataset in an unintended way. Common cases include:

- a key expected to be unique repeats and multiplies rows;
- an inner join removes records that have no match;
- an export changes `001` to `1`;
- missing and extra records cancel out, leaving the expected total row count;
- duplicate keys on both sides produce a many-to-many expansion.

TableProof makes the expected row relationship explicit and checks the files against it.

## Install

TableProof requires Python 3.11 or later.

```bash
python -m pip install tableproof
tableproof --version
```

From a source checkout:

```bash
python -m pip install .
```

## Basic use

Create a commented configuration file:

```bash
tableproof init
```

Run every audit in that file:

```bash
tableproof check --config tableproof.toml
```

Check one join without a configuration file:

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many
```

Check an existing result and write JSON:

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many \
  --result merged.tsv --join-type left \
  --format json --output tableproof-report.json
```

The repository example can run without installation:

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

`one-to-many` means the left key must be unique; repetition on the right is allowed. A 1:1 dataset also satisfies that constraint. `many-to-many` permits repetition on both sides, but TableProof still reports the resulting expansion.

Composite keys are ordered. Repeat `--left-key` and `--right-key` in direct mode, or use ordered arrays in TOML. If a result table uses different key columns, set `result_keys` or repeat `--result-key`.

## Checks

- UTF-8 and UTF-8 BOM decoding, delimiter, headers, and row width;
- missing, blank, single-column, and composite keys;
- duplicate groups and excess duplicate rows on each side;
- observed 1:1, 1:N, N:1, or N:N cardinality;
- left and right unmatched keys and rows;
- predicted rows and expansion factors for inner, left, right, and full joins;
- possible collisions after hypothetical trimming, case-folding, or leading-zero removal;
- expected and actual result-key multisets;
- SHA-256 hashes of input and result files.

Keys remain strings. TableProof does not trim, case-fold, parse numbers, remove leading zeros, deduplicate, or rewrite input files. A normalization warning identifies values to review; it does not establish that the records are equivalent.

## Reports and exit codes

Use `--format text|json|markdown` and `--output PATH`. JSON follows [Report Schema v1](schemas/tableproof-report-v1.schema.json) and omits a run timestamp, so the same files and settings produce the same report content.

- `0`: the configured threshold passed;
- `1`: the data violated a policy, or warnings exist with `--fail-on warning`;
- `2`: command, configuration, encoding, parsing, I/O, or result-key inference error.

Reports show counts and truncated SHA-256 key examples by default. `--show-raw-keys` and `[report].show_raw_keys = true` disclose original key values and should not be enabled in public CI without review.

## GitHub Action

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

The Action uses no API key and requests no write permission. It adds annotations and a job summary, writes JSON and Markdown reports, forces hashed key examples, and confines paths to `GITHUB_WORKSPACE`.

## Agent Skill

The Skill is stored at [`.agents/skills/table-proof`](.agents/skills/table-proof/SKILL.md) and follows the [Agent Skills open specification](https://agentskills.io/specification). The same Skill directory can be used by Codex, Claude Code, claude.ai, VS Code/GitHub Copilot, and other clients that implement the format, subject to each client's discovery path and execution environment.

- Codex and current VS Code/Copilot can discover the checked-in `.agents/skills/` path.
- Claude Code users can copy the directory to `.claude/skills/table-proof/`.
- claude.ai users can upload the directory as a ZIP.

See [Agent Skill setup](docs/AGENT_SKILL.md) for installation details and runtime limits. `agents/openai.yaml` is optional Codex UI metadata; the audit procedure is in the portable `SKILL.md`.

## Limits

- v0.1 reads CSV and TSV encoded as UTF-8 or UTF-8 with BOM.
- Key-frequency maps are kept in memory; very high-cardinality files can use substantial RAM.
- Blank key components never match, including another blank key.
- Result checks compare the declared key multiset. They do not verify the provenance of every non-key value.
- Hashed examples reduce disclosure but do not anonymize low-entropy identifiers.

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m tableproof check --config examples/tableproof.toml
```

CI covers Windows, Linux, macOS, and Python 3.11–3.14. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the factual [project evidence ledger](docs/CODEX_FOR_OSS_APPLICATION.md).

## License

MIT
