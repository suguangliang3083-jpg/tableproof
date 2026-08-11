# Join semantics used by TableProof

Load this reference when selecting a relationship, interpreting a materialized result, or explaining normalization warnings.

## The row entity comes first

A key is meaningful only relative to what one row represents. A unique `sample_id` may identify a biological specimen in a sample table, while the same value legitimately repeats in a measurement table because each row represents one assay result. Confirm the row entity and key provenance before assigning a cardinality constraint.

Uniqueness in one file is evidence about that file, not proof that the column is stable across instruments, exports, sites, or analysis stages. Prefer documented identifiers with a maintained namespace. For composite keys, preserve component order.

## Relationship constraints

- `one-to-one`: neither side may repeat a usable key.
- `one-to-many`: the left side must be unique; the right side may repeat. Current 1:1 data satisfies this constraint.
- `many-to-one`: the right side must be unique; the left side may repeat. Current 1:1 data satisfies this constraint.
- `many-to-many`: neither side has a uniqueness constraint. Review expansion even when this is intentional.

Blank key components are excluded from relationship inference because they never match. If no usable keys remain on either side, the observed relationship is `unknown` and the audit fails.

## Exact strings and normalization hazards

TableProof compares exact strings. It never trims whitespace, changes case, parses numbers, or removes leading zeros. Thus `001`, `1`, `Sample-A`, `sample-a`, and `sample-a ` are distinct.

A normalization warning means unmatched exact keys would collide under one hypothetical transformation. It is a review lead, not evidence that records represent the same entity. Confirm the upstream identifier rules before any repair.

## Predicted rows

For a nonblank matching key with left multiplicity `L` and right multiplicity `R`, a join emits `L × R` rows. Unmatched records add rows according to join type:

- `inner`: matching products only.
- `left`: inner rows plus unmatched left rows.
- `right`: inner rows plus unmatched right rows.
- `full`: inner rows plus unmatched rows from both sides.

Blank key rows never match, including another blank key row. They survive only on a preserved side.

## Materialized result validation

When a result is provided, TableProof computes the exact expected key multiset for the declared join type and compares it with the result. A row-count match alone is insufficient: equal numbers of missing and excess records can cancel out. Review both the row delta and key-multiset differences.

If left and right key names differ, specify `result_keys` in TOML or repeat `--result-key` on the command line. For a full join with coalesced keys, point `result_keys` to the coalesced result columns.

## Safe interpretation

Keep source data immutable. Propose repairs separately and require a new output file, explicit transformation provenance, and a rerun of the same audit. Do not choose duplicate survivors or infer biological equivalence from spelling similarity.
