from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tableproof.config import load_config
from tableproof.models import TableProofError

from common import write_table


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        write_table(self.root / "left.tsv", [["id"], ["A"]])
        write_table(self.root / "right.tsv", [["id"], ["A"]])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_config(self, body: str) -> Path:
        path = self.root / "tableproof.toml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_relative_paths_and_report_settings(self) -> None:
        path = self.write_config(
            """version = 1
[report]
show_raw_keys = false
sample_limit = 2
fail_on = "warning"
[[joins]]
name = "configured"
left = "left.tsv"
right = "right.tsv"
left_keys = ["id"]
right_keys = ["id"]
relationship = "one-to-one"
"""
        )
        specs, fail_on = load_config(path)
        self.assertEqual(fail_on, "warning")
        self.assertEqual(specs[0].left, (self.root / "left.tsv").resolve())
        self.assertEqual(specs[0].sample_limit, 2)

    def test_rejects_unknown_version(self) -> None:
        path = self.write_config("version = 2\n[[joins]]\n")
        with self.assertRaisesRegex(TableProofError, "version"):
            load_config(path)

    def test_result_requires_string_join_type(self) -> None:
        path = self.write_config(
            """version = 1
[[joins]]
left = "left.tsv"
right = "right.tsv"
left_keys = ["id"]
right_keys = ["id"]
relationship = "one-to-one"
result = "left.tsv"
join_type = ["left"]
"""
        )
        with self.assertRaisesRegex(TableProofError, "join_type"):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
