from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tableproof.audit import audit_join, audit_many

from common import spec, write_table


class RelationshipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def audit(self, left_ids: list[str], right_ids: list[str], expected: str):
        left = write_table(self.root / "left.tsv", [["id"], *[[value] for value in left_ids]])
        right = write_table(self.root / "right.tsv", [["id"], *[[value] for value in right_ids]])
        return audit_join(spec(left, right, expected))

    def test_one_to_one(self) -> None:
        report = self.audit(["A", "B"], ["A", "B"], "one-to-one")
        self.assertEqual(report["observed_relationship"], "one-to-one")
        self.assertEqual(report["verdict"], "pass")

    def test_one_to_many_accepts_one_to_one_as_narrower(self) -> None:
        report = self.audit(["A", "B"], ["A", "B"], "one-to-many")
        self.assertEqual(report["verdict"], "pass")
        self.assertIn("TP_RELATIONSHIP_NARROWER", {item["code"] for item in report["findings"]})

    def test_one_to_many(self) -> None:
        report = self.audit(["A", "B"], ["A", "A", "B"], "one-to-many")
        self.assertEqual(report["observed_relationship"], "one-to-many")
        self.assertEqual(report["right"]["duplicates"]["key_groups"], 1)

    def test_many_to_one(self) -> None:
        report = self.audit(["A", "A", "B"], ["A", "B"], "many-to-one")
        self.assertEqual(report["observed_relationship"], "many-to-one")
        self.assertEqual(report["verdict"], "pass")

    def test_unexpected_many_to_many_fails_and_predicts_expansion(self) -> None:
        report = self.audit(["A", "A", "B"], ["A", "A", "C"], "one-to-many")
        self.assertEqual(report["observed_relationship"], "many-to-many")
        self.assertEqual(report["predictions"]["inner"]["rows"], 4)
        self.assertEqual(report["verdict"], "fail")
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("TP_RELATIONSHIP_VIOLATION", codes)
        self.assertIn("TP_MANY_TO_MANY_EXPANSION", codes)

    def test_many_to_many_can_be_declared_but_still_warns(self) -> None:
        report = self.audit(["A", "A"], ["A", "A", "A"], "many-to-many")
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["summary"]["warnings"], 1)
        self.assertEqual(report["predictions"]["inner"]["rows"], 6)

    def test_disjoint_duplicates_do_not_claim_matching_row_explosion(self) -> None:
        report = self.audit(["A", "A"], ["B", "B"], "many-to-many")
        self.assertEqual(report["observed_relationship"], "many-to-many")
        self.assertNotIn(
            "TP_MANY_TO_MANY_EXPANSION", {item["code"] for item in report["findings"]}
        )

    def test_null_and_orphan_policies(self) -> None:
        left = write_table(self.root / "left.tsv", [["id"], [""], ["A"], ["L"]])
        right = write_table(self.root / "right.tsv", [["id"], ["A"], ["R"]])
        report = audit_join(
            spec(
                left,
                right,
                "one-to-one",
                left_unmatched="error",
                right_unmatched="warn",
                null_keys="error",
            )
        )
        self.assertEqual(report["left"]["null_key_rows"], 1)
        self.assertEqual(report["unmatched"]["left_rows"], 1)
        self.assertEqual(report["unmatched"]["right_rows"], 1)
        self.assertEqual(report["predictions"]["left"]["rows"], 3)
        self.assertEqual(report["verdict"], "fail")

    def test_composite_key(self) -> None:
        left = write_table(
            self.root / "left.csv",
            [["sample", "time"], ["S1", "T1"], ["S1", "T2"]],
        )
        right = write_table(
            self.root / "right.csv",
            [["sample", "time"], ["S1", "T1"], ["S1", "T1"], ["S1", "T2"]],
        )
        report = audit_join(
            spec(
                left,
                right,
                "one-to-many",
                left_keys=("sample", "time"),
                right_keys=("sample", "time"),
            )
        )
        self.assertEqual(report["observed_relationship"], "one-to-many")
        self.assertEqual(report["predictions"]["inner"]["rows"], 3)

    def test_normalization_hazards_are_report_only(self) -> None:
        left = write_table(self.root / "left.tsv", [["id"], ["001"], ["Alpha"], ["Beta "]])
        right = write_table(self.root / "right.tsv", [["id"], ["1"], ["alpha"], ["Beta"]])
        report = audit_join(spec(left, right, "one-to-one"))
        hazards = report["normalization_hazards"]
        self.assertEqual(hazards["leading_zero"]["groups"], 1)
        self.assertEqual(hazards["case"]["groups"], 1)
        self.assertEqual(hazards["whitespace"]["groups"], 1)
        self.assertEqual(report["predictions"]["inner"]["rows"], 0)

    def test_privacy_default_and_raw_opt_in(self) -> None:
        left = write_table(self.root / "left.tsv", [["id", "sensitive_diagnosis"], ["secret-subject", "x"]])
        right = write_table(self.root / "right.tsv", [["id"], ["different"]])
        hidden = audit_join(spec(left, right, "one-to-one"))
        hidden_text = str(hidden)
        self.assertNotIn("secret-subject", hidden_text)
        self.assertNotIn("sensitive_diagnosis", hidden_text)
        self.assertIn("sha256:", hidden_text)
        shown = audit_join(spec(left, right, "one-to-one", show_raw_keys=True))
        self.assertIn("secret-subject", str(shown))

    def test_top_level_report_is_deterministic(self) -> None:
        left = write_table(self.root / "left.tsv", [["id"], ["A"]])
        right = write_table(self.root / "right.tsv", [["id"], ["A"]])
        request = spec(left, right, "one-to-one")
        self.assertEqual(audit_many([request]), audit_many([request]))
        self.assertEqual(audit_many([request])["schema_version"], "1.0")


class ResultValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.left = write_table(self.root / "left.tsv", [["id"], ["A"], ["B"]])
        self.right = write_table(self.root / "right.tsv", [["id"], ["A"], ["A"], ["C"]])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_all_join_types(self) -> None:
        expected = {
            "inner": ["A", "A"],
            "left": ["A", "A", "B"],
            "right": ["A", "A", "C"],
            "full": ["A", "A", "B", "C"],
        }
        for join_type, ids in expected.items():
            with self.subTest(join_type=join_type):
                result = write_table(
                    self.root / f"result-{join_type}.tsv", [["id"], *[[value] for value in ids]]
                )
                report = audit_join(
                    spec(
                        self.left,
                        self.right,
                        "one-to-many",
                        result=result,
                        join_type=join_type,
                    )
                )
                self.assertEqual(report["result"]["actual_rows"], len(ids))
                self.assertEqual(report["result"]["missing_rows"], 0)
                self.assertEqual(report["result"]["excess_rows"], 0)
                self.assertEqual(report["verdict"], "pass")

    def test_wrong_result_multiset_fails_even_when_row_count_matches(self) -> None:
        result = write_table(self.root / "bad.tsv", [["id"], ["A"], ["A"], ["C"]])
        report = audit_join(
            spec(self.left, self.right, "one-to-many", result=result, join_type="left")
        )
        self.assertEqual(report["result"]["row_delta"], 0)
        self.assertEqual(report["result"]["missing_rows"], 1)
        self.assertEqual(report["result"]["excess_rows"], 1)
        self.assertEqual(report["verdict"], "fail")


if __name__ == "__main__":
    unittest.main()
