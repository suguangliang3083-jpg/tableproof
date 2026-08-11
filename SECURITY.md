# Security and privacy

## Supported versions

Security fixes are provided for the latest released minor line, currently `0.1.x`. Report unreleased regressions against the current default branch.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/suguangliang3083-jpg/tableproof/security/advisories/new). Do not include sensitive datasets, credentials, or exploit details in a public issue. If private reporting is temporarily unavailable, contact the maintainer through the [GitHub profile](https://github.com/suguangliang3083-jpg) without disclosing vulnerability details publicly.

## Threat model

TableProof reads untrusted CSV/TSV content but never executes formulas, macros, embedded code, or cell values. It performs no network requests and does not require secrets. Reports hash key examples by default.

Remaining risks include:

- memory or CPU exhaustion from very large/high-cardinality files or adversarial multiplicities;
- disk exhaustion when a caller chooses a report directory without quotas;
- sensitive header names, paths, counts, hashes, or explicitly enabled raw examples entering logs/artifacts;
- guessed low-entropy identifiers despite hashing;
- local CLI users intentionally pointing configuration paths at any file they can read.

The GitHub Action forces raw examples off and confines configuration, input, result, and report paths to the resolved `GITHUB_WORKSPACE`, including symlink resolution. It should run with `contents: read`, without secrets, and on `pull_request`—never `pull_request_target` for untrusted forks. Treat changes to `tableproof.toml`, workflow files, and Action versions as code changes requiring review.

## Safe CI defaults

- Keep `show_raw_keys = false`.
- Pin a reviewed major or commit; review moving-tag updates.
- Do not pass repository or cloud credentials because TableProof does not need them.
- Upload reports only when their metadata classification allows it.
- Apply runner time/storage limits for repositories accepting untrusted data changes.

Codex Security should be requested in an OpenAI program application only after this model has been reviewed against a published Action and real untrusted-PR use.
