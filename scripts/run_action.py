"""GitHub composite Action entrypoint; requires only Python 3.11+."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ACTION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_ROOT / "src"))

from tableproof.audit import audit_many  # noqa: E402
from tableproof.config import load_config  # noqa: E402
from tableproof.models import TableProofError  # noqa: E402
from tableproof.render import github_annotations, render_json, render_markdown  # noqa: E402


def _require_within(root: Path, candidate: Path, label: str) -> None:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise TableProofError(f"{label} must stay inside GITHUB_WORKSPACE: {candidate}") from exc


def _append_environment_file(name: str, lines: list[str]) -> None:
    destination = os.environ.get(name)
    if not destination:
        return
    with Path(destination).open("a", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def main() -> int:
    config = Path(os.environ.get("INPUT_CONFIG", "tableproof.toml"))
    report_dir = Path(os.environ.get("INPUT_REPORT_DIR", "tableproof-reports"))
    fail_on = os.environ.get("INPUT_FAIL_ON", "error")
    if fail_on not in {"error", "warning"}:
        print("::error title=TableProof configuration::fail-on must be error or warning")
        return 2
    try:
        workspace_value = os.environ.get("GITHUB_WORKSPACE")
        workspace = Path(workspace_value).resolve() if workspace_value else None
        if workspace:
            _require_within(workspace, config, "config")
            _require_within(workspace, report_dir, "report-dir")
        # CI annotations and artifacts never disclose raw example keys, even if an
        # untrusted pull request changes the repository configuration.
        specs, _ = load_config(config, show_raw_override=False)
        if workspace:
            for index, spec in enumerate(specs, start=1):
                _require_within(workspace, spec.left, f"joins[{index}].left")
                _require_within(workspace, spec.right, f"joins[{index}].right")
                if spec.result:
                    _require_within(workspace, spec.result, f"joins[{index}].result")
        report = audit_many(specs)
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = (report_dir / "tableproof-report.json").resolve()
        markdown_path = (report_dir / "tableproof-report.md").resolve()
        json_path.write_text(render_json(report), encoding="utf-8", newline="\n")
        markdown = render_markdown(report)
        markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
    except (TableProofError, OSError) as exc:
        safe = str(exc).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=TableProof configuration::{safe}")
        return 2

    for annotation in github_annotations(report):
        print(annotation)
    _append_environment_file("GITHUB_STEP_SUMMARY", [markdown])
    _append_environment_file(
        "GITHUB_OUTPUT",
        [
            f"report-json={json_path}",
            f"report-markdown={markdown_path}",
            f"verdict={report['verdict']}",
            f"errors={report['summary']['errors']}",
            f"warnings={report['summary']['warnings']}",
        ],
    )
    print(f"TableProof report: {markdown_path}")
    if report["summary"]["errors"]:
        return 1
    if fail_on == "warning" and report["summary"]["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
