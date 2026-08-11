---
name: table-proof
description: Check CSV or TSV joins with the tableproof CLI. Use when an agent needs to assess duplicate or blank keys, expected one-to-one/one-to-many/many-to-one/many-to-many relationships, unmatched records, predicted row counts, normalization risks, or an existing inner/left/right/full join result.
---

# Audit a table join

Use `tableproof` for the audit result. Do not replace it with visual inspection or model judgment.

## Confirm the contract

Before running the command, confirm:

- what one row represents in each table;
- the left and right key columns, in order;
- why those keys should remain stable across collection, export, and analysis;
- the allowed relationship: `one-to-one`, `one-to-many`, `many-to-one`, or `many-to-many`;
- the policy for unmatched rows and blank key components;
- the join type when checking an existing result.

Ask only for missing information. A column that happens to be unique in one file is not automatically a stable identifier.

Read [references/join-semantics.md](references/join-semantics.md) before choosing a relationship, interpreting result-table differences, or explaining normalization warnings.

## Boundaries

- Do not install software without permission.
- Do not rewrite, trim, case-fold, deduplicate, aggregate, or overwrite input tables during an audit.
- Do not convert identifiers to numbers or remove leading zeros.
- Do not treat a normalization warning as proof that two identifiers refer to the same record.
- Do not expose raw key examples unless the user has approved that disclosure.
- Do not use this Skill as a substitute for checking non-key column provenance or scientific identifier policy.

## Run the audit

Use a repository configuration when available:

```text
tableproof check --config tableproof.toml --format json --output tableproof-report.json
```

For one join:

```text
tableproof check --left A.tsv --right B.tsv --left-key id --right-key id --expect one-to-many --format json
```

Repeat the key options in the same component order for composite keys. Add `--result merged.tsv --join-type left` only when checking an existing output. Use `--result-key` when the result key cannot be inferred.

If the executable is unavailable, try `python -m tableproof` only when the package is already installed. In a TableProof source checkout, use the repository's documented `PYTHONPATH=src` form. Otherwise stop and explain the missing runtime requirement.

Exit codes:

- `0`: the configured failure threshold passed;
- `1`: the data violated an audit policy;
- `2`: the command, configuration, input, or result could not be read correctly. Resolve this before interpreting the data.

## Report the result

Give the user:

1. the confirmed join contract;
2. the CLI verdict and exit code;
3. the observed relationship and duplicate/null counts;
4. left and right unmatched counts;
5. predicted rows for inner, left, right, and full joins;
6. result row or key-multiset differences, when checked;
7. a short explanation of the records at risk;
8. separate next steps, without modifying the inputs.

Hashed key examples help match findings across reports. They do not reveal the source value, but they are not an anonymization guarantee.

For worked command choices and acceptance checks, read [references/examples.md](references/examples.md).

## Handle repair requests

When the user asks for a repair, propose the transformation first. Specify a new output path, the exact rule, provenance columns, and the audit that will be rerun. Keep the original files unchanged.
