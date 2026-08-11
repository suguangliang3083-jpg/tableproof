# Codex for Open Source application evidence ledger

Use this document only after TableProof is public. Replace every placeholder with a current, public URL or an honest zero. Delete inapplicable claims; never estimate upward.

## Submission snapshot

**Checked at (UTC):** `2026-08-11T13:07:44Z; refresh immediately before submission`

**Repository:** `https://github.com/suguangliang3083-jpg/tableproof`  
**Applicant GitHub account:** `https://github.com/suguangliang3083-jpg`  
**Maintainer permission evidence:** `Repository owner; verify on the public repository and release pages before submission`

| Metric | Current value | Public evidence | Counting rule |
|---|---:|---|---|
| GitHub stars | `0` | `https://github.com/suguangliang3083-jpg/tableproof` | Checked after v0.1.1 publication; refresh at submission; no exchanges or paid/automated stars. |
| PyPI downloads | `Not yet measured` | `https://pypi.org/project/tableproof/` | Do not infer a total from release existence; state the exact period and statistics source when reporting. |
| Independent public adopting repositories | `0` | `None yet` | Exclude TableProof-owned demos and forks without actual configuration/use. |
| Verifiable user case studies | `0` | `None yet` | Public, consented, reproducible description. |
| Published releases | `2 (v0.1.0, v0.1.1)` | `https://github.com/suguangliang3083-jpg/tableproof/releases` | Count public GitHub releases only. |
| Feedback-driven releases after v0.1 | `0 independently verifiable` | `None yet` | v0.1.1 responded to maintainer feedback, but no public feedback source is available, so it is not counted here. |
| Substantive issues/discussions handled | `0` | `None yet` | Exclude spam, duplicate bookkeeping, and self-created padding. |
| Active contributors | `1 initial maintainer` | `https://github.com/suguangliang3083-jpg/tableproof/graphs/contributors` | Refresh after publication using GitHub's displayed definition. |

## Draft project description

TableProof is a dependency-free CLI for checking CSV/TSV joins in research and data pipelines. It reports blank and duplicate keys, observed 1:1/1:N/N:1/N:N cardinality, unmatched records, predicted row counts, and key-multiset differences in an existing result. The GitHub Action runs the same checks in CI. The Agent Skill asks users to state the row entities, keys, and expected relationship before it invokes the CLI. Audits do not modify source data, and reports hash key examples by default.

## Ecosystem importance

Replace this section with evidence from the ledger. Explain which independent workflows rely on the tool, what silent failures were caught, and how maintainers responded. Do not use stars alone as evidence of importance.

## How requested API credits would support OSS maintenance

API credits would be used only for TableProof maintenance: reviewing proposed join rules in pull requests, classifying public issues, turning consented real-world failures into minimal tests, evaluating regressions in the TableProof Skill, and preparing release notes or contributor guidance. The OpenAI API would not determine data verdicts; all CSV/TSV findings would continue to come from the deterministic local engine. Usage would avoid uploading private research data and would be documented in repository policy.

## ChatGPT Pro and Codex Security

Request ChatGPT Pro only if it will be used for ongoing public maintenance. Request Codex Security only after the published GitHub Action's untrusted-input threat model has been reviewed and the application accurately describes its CI exposure. Do not imply that either benefit is guaranteed.

## Pre-submission checklist

- Re-read the live [program page](https://developers.openai.com/community/codex-for-oss), [terms](https://learn.chatgpt.com/docs/codex-for-oss-terms), and current application form.
- Confirm the applicant has the required repository maintenance authority.
- Confirm every metric and URL on the same day as submission.
- Remove placeholder URLs from package metadata, changelog, and Action examples.
- Confirm the MIT license, public issue tracker, security contact, release history, and recent maintenance activity are visible.
- Disclose that `100 stars` was an outreach target, not an official eligibility threshold.
- Save a copy of the submitted factual snapshot and update it if OpenAI requests clarification.

Selection is not guaranteed. Program availability, criteria, benefits, and terms can change.
