"""Human and machine report rendering."""

from __future__ import annotations

import json
from typing import Any


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"TableProof {report['tool']['version']}: {report['verdict'].upper()}",
        f"Audits: {summary['audits']} | errors: {summary['errors']} | warnings: {summary['warnings']} | info: {summary['infos']}",
    ]
    for audit in report["audits"]:
        lines.extend(
            [
                "",
                f"[{audit['verdict'].upper()}] {audit['name']}",
                f"  relationship: expected {audit['expected_relationship']}, observed {audit['observed_relationship']}",
                f"  rows: left {audit['left']['rows']}, right {audit['right']['rows']}",
                f"  unmatched rows: left {audit['unmatched']['left_rows']}, right {audit['unmatched']['right_rows']}",
                "  predictions: "
                + ", ".join(
                    f"{name}={data['rows']}" for name, data in audit["predictions"].items()
                ),
            ]
        )
        if audit["result"]:
            result = audit["result"]
            lines.append(
                f"  result ({result['join_type']}): expected {result['expected_rows']}, actual {result['actual_rows']}"
            )
        for finding in audit["findings"]:
            lines.append(f"  - {finding['severity'].upper()} {finding['code']}: {finding['message']}")
    return "\n".join(lines) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# TableProof report",
        "",
        f"**Verdict:** `{report['verdict']}`  ",
        f"**Tool:** `{report['tool']['name']} {report['tool']['version']}`  ",
        f"**Audits:** {summary['audits']} · **Errors:** {summary['errors']} · **Warnings:** {summary['warnings']} · **Info:** {summary['infos']}",
        "",
    ]
    for audit in report["audits"]:
        lines.extend(
            [
                f"## {audit['name']}",
                "",
                f"Verdict: **{audit['verdict']}**",
                "",
                "| Check | Value |",
                "|---|---:|",
                f"| Expected relationship | `{audit['expected_relationship']}` |",
                f"| Observed relationship | `{audit['observed_relationship']}` |",
                f"| Left rows | {audit['left']['rows']} |",
                f"| Right rows | {audit['right']['rows']} |",
                f"| Left unmatched rows | {audit['unmatched']['left_rows']} |",
                f"| Right unmatched rows | {audit['unmatched']['right_rows']} |",
                f"| Predicted inner rows | {audit['predictions']['inner']['rows']} |",
                f"| Predicted left rows | {audit['predictions']['left']['rows']} |",
                f"| Predicted right rows | {audit['predictions']['right']['rows']} |",
                f"| Predicted full rows | {audit['predictions']['full']['rows']} |",
                "",
                "### Findings",
                "",
            ]
        )
        if not audit["findings"]:
            lines.append("No findings.")
        else:
            for finding in audit["findings"]:
                lines.append(
                    f"- **{finding['severity'].upper()} · `{finding['code']}`** — {finding['message']}"
                )
        if audit["result"]:
            result = audit["result"]
            lines.extend(
                [
                    "",
                    "### Materialized result",
                    "",
                    f"Declared `{result['join_type']}` join: expected **{result['expected_rows']}** rows; found **{result['actual_rows']}** (delta {result['row_delta']}).",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render(report: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return render_json(report)
    if output_format == "markdown":
        return render_markdown(report)
    if output_format == "text":
        return render_text(report)
    raise ValueError(f"Unsupported output format: {output_format}")


def github_annotations(report: dict[str, Any]) -> list[str]:
    """Render workflow-command annotations without exposing raw key context."""

    annotations: list[str] = []
    for audit in report["audits"]:
        for finding in audit["findings"]:
            if finding["severity"] not in {"error", "warn"}:
                continue
            command = "error" if finding["severity"] == "error" else "warning"
            title = _escape_command(f"TableProof {finding['code']}")
            message = _escape_command(f"{audit['name']}: {finding['message']}")
            annotations.append(f"::{command} title={title}::{message}")
    return annotations


def _escape_command(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
