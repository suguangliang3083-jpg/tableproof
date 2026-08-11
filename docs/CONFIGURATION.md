# Configuration reference

TableProof configuration is TOML with `version = 1`. Relative file paths are resolved from the configuration file's directory.

## Report settings

```toml
[report]
show_raw_keys = false # explicit privacy disclosure switch
sample_limit = 5      # examples per finding; zero disables examples
fail_on = "error"     # error or warning
```

Command-line `--show-raw-keys` enables raw examples for that run. There is intentionally no CLI switch that silently turns a configured disclosure off: review shared configurations before public CI use.

## Join fields

| Field | Required | Allowed values / meaning |
|---|---|---|
| `name` | No | Human-readable audit name; defaults to `join-N`. |
| `left`, `right` | Yes | UTF-8 `.csv` or `.tsv` paths. |
| `left_keys`, `right_keys` | Yes | Ordered arrays of equal length. |
| `relationship` | Yes | `one-to-one`, `one-to-many`, `many-to-one`, `many-to-many`. |
| `left_unmatched` | No | `error`, `warn`, `ignore`; default `warn`. |
| `right_unmatched` | No | `error`, `warn`, `ignore`; default `warn`. |
| `null_keys` | No | Policy applied separately to both sides; default `error`. |
| `result` | No | Existing materialized join to verify. |
| `join_type` | With `result` | `inner`, `left`, `right`, `full`. |
| `result_keys` | No | Ordered result-key columns when they cannot be inferred. |

An empty string in any key component makes that row a null-key row. Whitespace-only strings are not empty and remain exact keys, but a cross-table whitespace collision may be reported.

## Direct mode

Repeat key switches for composite keys:

```bash
tableproof check \
  --left observations.tsv --right taxonomy.tsv \
  --left-key study_id --left-key sample_id \
  --right-key study_id --right-key sample_id \
  --expect many-to-one
```

Comma-separated values are also accepted. Component order must match across sides.
