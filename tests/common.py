from __future__ import annotations

import csv
from pathlib import Path

from tableproof.models import JoinSpec


def write_table(path: Path, rows: list[list[str]], *, delimiter: str | None = None) -> Path:
    delimiter = delimiter or ("\t" if path.suffix == ".tsv" else ",")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter, lineterminator="\n")
        writer.writerows(rows)
    return path


def spec(
    left: Path,
    right: Path,
    relationship: str,
    *,
    left_keys: tuple[str, ...] = ("id",),
    right_keys: tuple[str, ...] = ("id",),
    **kwargs: object,
) -> JoinSpec:
    defaults: dict[str, object] = {
        "name": "test-join",
        "left": left,
        "right": right,
        "left_keys": left_keys,
        "right_keys": right_keys,
        "relationship": relationship,
        "left_unmatched": "ignore",
        "right_unmatched": "ignore",
        "null_keys": "error",
    }
    defaults.update(kwargs)
    return JoinSpec(**defaults)  # type: ignore[arg-type]
