from __future__ import annotations

import codecs
import tempfile
import unittest
from pathlib import Path

from tableproof.audit import read_table
from tableproof.models import TableProofError


class ParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_utf8_bom_crlf_and_quoted_delimiter(self) -> None:
        path = self.root / "quoted.csv"
        path.write_bytes(codecs.BOM_UTF8 + b'id,note\r\nA,"x,y"\r\n')
        table = read_table(path, ("id",))
        self.assertEqual(table.header, ("id", "note"))
        self.assertEqual(table.row_count, 1)

    def test_empty_file(self) -> None:
        path = self.root / "empty.tsv"
        path.write_bytes(b"")
        with self.assertRaises(TableProofError):
            read_table(path, ("id",))

    def test_duplicate_column_names(self) -> None:
        path = self.root / "duplicate.csv"
        path.write_text("id,id\nA,A\n", encoding="utf-8")
        with self.assertRaisesRegex(TableProofError, "duplicate column"):
            read_table(path, ("id",))

    def test_repeated_header_row(self) -> None:
        path = self.root / "repeated.tsv"
        path.write_text("id\nA\nid\n", encoding="utf-8")
        with self.assertRaisesRegex(TableProofError, "Repeated header"):
            read_table(path, ("id",))

    def test_broken_row_width(self) -> None:
        path = self.root / "broken.tsv"
        path.write_text("id\tvalue\nA\n", encoding="utf-8")
        with self.assertRaisesRegex(TableProofError, "Row width mismatch"):
            read_table(path, ("id",))

    def test_malformed_quote(self) -> None:
        path = self.root / "broken.csv"
        path.write_text('id,note\nA,"unterminated\n', encoding="utf-8")
        with self.assertRaises(TableProofError):
            read_table(path, ("id",))

    def test_invalid_utf8(self) -> None:
        path = self.root / "invalid.csv"
        path.write_bytes(b"id\n\xff\n")
        with self.assertRaises(TableProofError):
            read_table(path, ("id",))

    def test_missing_key_column(self) -> None:
        path = self.root / "missing.tsv"
        path.write_text("other\nA\n", encoding="utf-8")
        with self.assertRaisesRegex(TableProofError, "Missing key columns"):
            read_table(path, ("id",))


if __name__ == "__main__":
    unittest.main()
