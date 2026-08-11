"""Data models shared by the parser, auditor, and CLI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

Key = tuple[str, ...]


class TableProofError(Exception):
    """A configuration, parsing, or I/O error that maps to exit code 2."""


@dataclass(frozen=True)
class JoinSpec:
    """A fully validated join audit request."""

    name: str
    left: Path
    right: Path
    left_keys: tuple[str, ...]
    right_keys: tuple[str, ...]
    relationship: str
    left_unmatched: str = "warn"
    right_unmatched: str = "warn"
    null_keys: str = "error"
    result: Path | None = None
    join_type: str | None = None
    result_keys: tuple[str, ...] | None = None
    show_raw_keys: bool = False
    sample_limit: int = 5


@dataclass
class TableData:
    """Parsed table metadata and exact key multiplicities."""

    path: Path
    sha256: str
    delimiter: str
    header: tuple[str, ...]
    row_count: int
    key_columns: tuple[str, ...]
    keys: Counter[Key]

    @property
    def column_count(self) -> int:
        return len(self.header)

    @property
    def null_rows(self) -> int:
        return sum(count for key, count in self.keys.items() if any(part == "" for part in key))

    @property
    def usable_keys(self) -> Counter[Key]:
        return Counter({key: count for key, count in self.keys.items() if all(part != "" for part in key)})
