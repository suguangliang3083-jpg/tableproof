from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tableproof.cli import main
from tableproof.render import github_annotations, render_json
from tableproof.audit import audit_many

from common import spec, write_table


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.left = write_table(self.root / "left.tsv", [["id"], ["A"], ["B"]])
        self.right = write_table(self.root / "right.tsv", [["id"], ["A"], ["B"]])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_direct_pass_exit_zero_and_stable_json(self) -> None:
        args = [
            "check",
            "--left",
            str(self.left),
            "--right",
            str(self.right),
            "--left-key",
            "id",
            "--right-key",
            "id",
            "--expect",
            "one-to-one",
            "--format",
            "json",
        ]
        first = self.run_cli(args)
        second = self.run_cli(args)
        self.assertEqual(first[0], 0)
        self.assertEqual(first[1], second[1])
        self.assertEqual(json.loads(first[1])["verdict"], "pass")

    def test_policy_violation_exit_one(self) -> None:
        right = write_table(self.root / "repeated.tsv", [["id"], ["A"], ["A"], ["B"]])
        code, _, _ = self.run_cli(
            [
                "check",
                "--left",
                str(self.left),
                "--right",
                str(right),
                "--left-key",
                "id",
                "--right-key",
                "id",
                "--expect",
                "one-to-one",
            ]
        )
        self.assertEqual(code, 1)

    def test_parse_or_io_error_exit_two(self) -> None:
        code, _, stderr = self.run_cli(
            [
                "check",
                "--left",
                str(self.root / "missing.tsv"),
                "--right",
                str(self.right),
                "--left-key",
                "id",
                "--right-key",
                "id",
                "--expect",
                "one-to-one",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("error", stderr)

    def test_fail_on_warning(self) -> None:
        right = write_table(self.root / "orphan.tsv", [["id"], ["A"], ["C"]])
        code, _, _ = self.run_cli(
            [
                "check",
                "--left",
                str(self.left),
                "--right",
                str(right),
                "--left-key",
                "id",
                "--right-key",
                "id",
                "--expect",
                "one-to-one",
                "--fail-on",
                "warning",
            ]
        )
        self.assertEqual(code, 1)

    def test_init_refuses_overwrite(self) -> None:
        config = self.root / "tableproof.toml"
        self.assertEqual(self.run_cli(["init", "--path", str(config)])[0], 0)
        self.assertEqual(self.run_cli(["init", "--path", str(config)])[0], 2)
        self.assertIn("version = 1", config.read_text(encoding="utf-8"))

    def test_output_file(self) -> None:
        output = self.root / "report.md"
        code, stdout, _ = self.run_cli(
            [
                "check",
                "--left",
                str(self.left),
                "--right",
                str(self.right),
                "--left-key",
                "id",
                "--right-key",
                "id",
                "--expect",
                "one-to-one",
                "--format",
                "markdown",
                "--output",
                str(output),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertIn("# TableProof report", output.read_text(encoding="utf-8"))


class RenderingAndActionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_annotations_do_not_include_raw_context(self) -> None:
        left = write_table(self.root / "left.tsv", [["id"], ["secret"]])
        right = write_table(self.root / "right.tsv", [["id"], ["other"]])
        report = audit_many(
            [spec(left, right, "one-to-one", left_unmatched="error", right_unmatched="warn")]
        )
        annotations = "\n".join(github_annotations(report))
        self.assertIn("::error", annotations)
        self.assertIn("::warning", annotations)
        self.assertNotIn("secret", annotations)

    def test_json_has_required_fixed_fields(self) -> None:
        left = write_table(self.root / "left.tsv", [["id"], ["A"]])
        right = write_table(self.root / "right.tsv", [["id"], ["A"]])
        report = json.loads(render_json(audit_many([spec(left, right, "one-to-one")])))
        audit = report["audits"][0]
        for field in (
            "keys",
            "expected_relationship",
            "observed_relationship",
            "left",
            "right",
            "unmatched",
            "predictions",
            "findings",
            "verdict",
        ):
            self.assertIn(field, audit)
        self.assertEqual(len(audit["left"]["sha256"]), 64)

    def test_action_wrapper_writes_reports_summary_outputs_and_annotations(self) -> None:
        project = Path(__file__).resolve().parents[1]
        reports = self.root / "reports"
        outputs = self.root / "github-output.txt"
        summary = self.root / "summary.md"
        data = self.root / "data"
        data.mkdir()
        write_table(data / "left.tsv", [["id"], ["private-subject"], ["B"]])
        write_table(data / "right.tsv", [["id"], ["A"], ["C"]])
        config = self.root / "tableproof.toml"
        config.write_text(
            """version = 1
[report]
show_raw_keys = true
[[joins]]
name = "action-test"
left = "data/left.tsv"
right = "data/right.tsv"
left_keys = ["id"]
right_keys = ["id"]
relationship = "one-to-one"
left_unmatched = "warn"
right_unmatched = "warn"
null_keys = "error"
""",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.update(
            {
                "INPUT_CONFIG": str(config),
                "INPUT_FAIL_ON": "error",
                "INPUT_REPORT_DIR": str(reports),
                "GITHUB_OUTPUT": str(outputs),
                "GITHUB_STEP_SUMMARY": str(summary),
                "GITHUB_WORKSPACE": str(self.root),
            }
        )
        completed = subprocess.run(
            [sys.executable, str(project / "scripts" / "run_action.py")],
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("::warning", completed.stdout)
        self.assertTrue((reports / "tableproof-report.json").exists())
        self.assertNotIn(
            "private-subject", (reports / "tableproof-report.json").read_text(encoding="utf-8")
        )
        self.assertIn("verdict=pass", outputs.read_text(encoding="utf-8"))
        self.assertIn("# TableProof report", summary.read_text(encoding="utf-8"))

    def test_action_manifest_has_public_inputs(self) -> None:
        manifest = (Path(__file__).resolve().parents[1] / "action.yml").read_text(encoding="utf-8")
        for name in ("config:", "fail-on:", "report-dir:"):
            self.assertIn(name, manifest)
        self.assertNotIn("api-key", manifest.lower())

    def test_action_rejects_config_outside_github_workspace(self) -> None:
        project = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.update(
            {
                "INPUT_CONFIG": str(project / "examples" / "tableproof.toml"),
                "INPUT_FAIL_ON": "error",
                "INPUT_REPORT_DIR": "reports",
                "GITHUB_WORKSPACE": str(self.root),
            }
        )
        completed = subprocess.run(
            [sys.executable, str(project / "scripts" / "run_action.py")],
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("inside GITHUB_WORKSPACE", completed.stdout)


if __name__ == "__main__":
    unittest.main()
