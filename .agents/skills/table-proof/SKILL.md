---
name: table-proof
description: Audit CSV or TSV joins before or after merging. Use for scientific table integration, metadata joins, row-loss checks, duplicate-key detection, join cardinality validation, orphan-key analysis, many-to-many expansion, or verification of an inner, left, right, or full result table.
---

# TableProof

Use the deterministic `tableproof` CLI to establish facts, then explain their scientific meaning. Never use an LLM judgment as the data verdict.

## 1. Establish the join contract

Before running an audit, obtain or confirm all of the following:

- What entity does one row represent on the left?
- What entity does one row represent on the right?
- Which column or ordered composite columns form each join key?
- Why is that key scientifically stable across collection, export, and analysis stages?
- What relationship is allowed: `one-to-one`, `one-to-many`, `many-to-one`, or `many-to-many`?
- How should unmatched left keys, unmatched right keys, and blank key components be treated?

If the user already supplied these facts, restate the contract briefly and continue. Do not treat an apparently unique column as a scientifically stable primary key without confirmation.

Read [references/join-semantics.md](references/join-semantics.md) when choosing a relationship, interpreting a materialized result, or explaining a normalization hazard.

## 2. Run the deterministic audit

Prefer a repository configuration when one exists:

```text
tableproof check --config tableproof.toml --format json --output tableproof-report.json
```

For a one-off audit, run:

```text
tableproof check --left A.tsv --right B.tsv --left-key id --right-key id --expect one-to-many --format json
```

For a composite key, repeat each key option in the same component order. Add `--result merged.tsv --join-type left` only when verifying an existing output. Use `--result-key` if the result key name cannot be inferred.

If the package is not installed but the current repository is TableProof, run `python -m tableproof` with the repository's `src` directory on `PYTHONPATH`. Otherwise, explain that `tableproof` must be installed; do not silently install software.

Treat exit codes as follows:

- `0`: the configured failure threshold passed.
- `1`: data violated an audit policy.
- `2`: configuration, parsing, encoding, I/O, or CLI usage error; fix this before interpreting the data.

## 3. Explain findings without changing data

Report the declared and observed relationship, duplicate/null counts, left and right orphan counts, all four predicted output sizes, expansion factors, and any result multiset differences. Explain which scientific records could be dropped, duplicated, or mis-associated.

Keep raw key examples hidden unless the user explicitly approves disclosure. Hashed examples are identifiers for comparing findings, not recoverable source values.

Separate recommendations from mutations. By default:

- Do not rewrite, trim, case-fold, deduplicate, aggregate, or overwrite source tables.
- Do not choose a surviving duplicate row.
- Do not convert identifiers to numbers or remove leading zeros.
- Do not describe normalization collisions as confirmed matches.

If the user requests a repair, first propose a new output path, an explicit transformation rule, provenance columns, and acceptance checks. Preserve the original files.
