# Examples

Use these examples to select a command and define an acceptance check. Replace paths and keys with the user's contract.

## Check a planned one-to-many join

Input: one row per sample on the left; one row per assay result on the right; `sample_id` is the shared key.

```text
tableproof check --left samples.tsv --right results.tsv --left-key sample_id --right-key sample_id --expect one-to-many --format json
```

Accept when the left key is unique, blank-key policy passes, and unmatched-row findings agree with the declared policy. Repetition on the right is allowed.

## Investigate an unexpected many-to-many relationship

Input: both tables were expected to contain one row per subject, but the CLI reports `many-to-many`.

Report the duplicate groups and predicted expansion. Do not select duplicate survivors. Ask whether the row entity was stated incorrectly or whether a missing key component should be added.

Accept only after the contract is corrected or a new audit passes with the intended relationship.

## Check an existing left-join result

```text
tableproof check --left samples.tsv --right results.tsv --left-key sample_id --right-key sample_id --expect one-to-many --result merged.tsv --join-type left --format json
```

Compare both row count and key multiset. Equal total rows do not pass when expected keys are missing and different keys are present in excess.
