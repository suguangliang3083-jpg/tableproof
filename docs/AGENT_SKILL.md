# Using the TableProof Agent Skill

TableProof follows the [Agent Skills open specification](https://agentskills.io/specification). The portable part is the `table-proof` directory: `SKILL.md`, `references/`, and any future `scripts/` or `assets/`. The `agents/openai.yaml` file only supplies optional Codex interface text; the audit procedure does not depend on it.

## Runtime requirement

The Skill instructs an agent to run the deterministic `tableproof` CLI. The agent's execution environment therefore needs Python 3.11 or later and TableProof installed or available from a source checkout.

```bash
python -m pip install tableproof
```

The Skill does not install the package without permission. A client may support the Agent Skills format but still lack a shell, Python, filesystem access, or package installation. In that case it can explain the contract but cannot produce a TableProof verdict.

## Install by client

The checked-in source is [`.agents/skills/table-proof`](../.agents/skills/table-proof/SKILL.md). Keep the directory intact when copying or uploading it.

| Client | Project installation |
|---|---|
| Codex | Use the checked-in `.agents/skills/table-proof/` directory. |
| VS Code / GitHub Copilot | Current VS Code discovers `.agents/skills/`, `.github/skills/`, and `.claude/skills/`; no copy is required for this repository. |
| Claude Code | Copy `table-proof/` to `.claude/skills/table-proof/`. |
| claude.ai | Zip the contents of `table-proof/` so `SKILL.md` is at the ZIP root, then upload it in the custom Skills settings. |
| Other compatible agents | Copy the same directory to the client-specific Skill location documented by that client. |

Discovery paths are client behavior, not part of the open file-format specification. Check the client's current documentation before claiming support.

## Package for upload

PowerShell:

```powershell
Compress-Archive -Path .agents/skills/table-proof/* -DestinationPath table-proof-skill.zip
```

macOS or Linux:

```bash
cd .agents/skills/table-proof
zip -r ../../../table-proof-skill.zip .
```

Inspect the ZIP before uploading. It should contain `SKILL.md`, `references/join-semantics.md`, `references/examples.md`, and the optional `agents/openai.yaml` file.

## Compatibility policy

TableProof claims compatibility with the Agent Skills file format. Client-specific discovery and tool execution are tested separately. New platform adapters may be added under `agents/`; the portable instructions remain in `SKILL.md`.
