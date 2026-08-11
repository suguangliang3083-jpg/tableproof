"""TOML configuration loading for TableProof."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .audit import validate_spec
from .models import JoinSpec, TableProofError


def _string_list(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        values = tuple(value)
    else:
        raise TableProofError(f"{field} must be a string or a list of strings")
    if not values or any(item == "" for item in values):
        raise TableProofError(f"{field} must contain at least one non-empty column name")
    return values


def _resolve(base: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise TableProofError(f"{field} must be a non-empty path string")
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _optional_path(base: Path, value: Any, field: str) -> Path | None:
    if value is None:
        return None
    return _resolve(base, value, field)


def load_config(path: Path, *, show_raw_override: bool | None = None) -> tuple[list[JoinSpec], str]:
    """Load and validate a v1 TableProof configuration."""

    try:
        with path.open("rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise TableProofError(f"Cannot load configuration {path}: {exc}") from exc
    if document.get("version") != 1:
        raise TableProofError("Configuration version must be 1")
    joins = document.get("joins")
    if not isinstance(joins, list) or not joins:
        raise TableProofError("Configuration must contain at least one [[joins]] table")
    report_settings = document.get("report", {})
    if not isinstance(report_settings, dict):
        raise TableProofError("[report] must be a table")
    show_raw_default = report_settings.get("show_raw_keys", False)
    sample_limit_default = report_settings.get("sample_limit", 5)
    fail_on = report_settings.get("fail_on", "error")
    if not isinstance(show_raw_default, bool):
        raise TableProofError("report.show_raw_keys must be true or false")
    if not isinstance(sample_limit_default, int) or isinstance(sample_limit_default, bool):
        raise TableProofError("report.sample_limit must be an integer")
    if fail_on not in {"error", "warning"}:
        raise TableProofError("report.fail_on must be error or warning")

    base = path.resolve().parent
    specs: list[JoinSpec] = []
    for index, raw in enumerate(joins, start=1):
        if not isinstance(raw, dict):
            raise TableProofError(f"joins entry {index} must be a table")
        try:
            left = _resolve(base, raw.get("left"), f"joins[{index}].left")
            right = _resolve(base, raw.get("right"), f"joins[{index}].right")
            left_keys = _string_list(raw.get("left_keys"), f"joins[{index}].left_keys")
            right_keys = _string_list(raw.get("right_keys"), f"joins[{index}].right_keys")
            relationship = raw.get("relationship")
            if not isinstance(relationship, str):
                raise TableProofError(f"joins[{index}].relationship must be a string")
            result_keys = raw.get("result_keys")
            spec = JoinSpec(
                name=str(raw.get("name", f"join-{index}")),
                left=left,
                right=right,
                left_keys=left_keys,
                right_keys=right_keys,
                relationship=relationship,
                left_unmatched=str(raw.get("left_unmatched", "warn")),
                right_unmatched=str(raw.get("right_unmatched", "warn")),
                null_keys=str(raw.get("null_keys", "error")),
                result=_optional_path(base, raw.get("result"), f"joins[{index}].result"),
                join_type=raw.get("join_type"),
                result_keys=_string_list(result_keys, f"joins[{index}].result_keys")
                if result_keys is not None
                else None,
                show_raw_keys=show_raw_default if show_raw_override is None else show_raw_override,
                sample_limit=sample_limit_default,
            )
        except TableProofError:
            raise
        validate_spec(spec)
        specs.append(spec)
    return specs, fail_on


CONFIG_TEMPLATE = '''# TableProof configuration v1
# Paths are resolved relative to this file.
version = 1

[report]
# Keep false in CI unless raw key disclosure has been reviewed.
show_raw_keys = false
sample_limit = 5
fail_on = "error"

[[joins]]
name = "samples-to-results"
left = "data/samples.tsv"
right = "data/results.tsv"
left_keys = ["sample_id"]
right_keys = ["sample_id"]
# Cardinality constraint: one-to-one, one-to-many, many-to-one, or many-to-many.
relationship = "one-to-many"
left_unmatched = "error"  # error, warn, or ignore
right_unmatched = "warn"
null_keys = "error"
# To verify a materialized result, uncomment both fields:
# result = "data/merged.tsv"
# join_type = "left"      # inner, left, right, or full
# result_keys = ["sample_id"]  # optional when inferable
'''
