"""Deterministic CSV/TSV join auditing."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Iterable

from . import __version__
from .models import JoinSpec, Key, TableData, TableProofError

RELATIONSHIPS = {"one-to-one", "one-to-many", "many-to-one", "many-to-many"}
JOIN_TYPES = {"inner", "left", "right", "full"}
POLICIES = {"error", "warn", "ignore"}


def _delimiter_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".tsv":
        return "\t"
    if suffix == ".csv":
        return ","
    raise TableProofError(f"Unsupported table extension for {path}: expected .csv or .tsv")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise TableProofError(f"Cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def read_header(path: Path) -> tuple[str, ...]:
    """Read and validate only the header of a CSV or TSV file."""

    delimiter = _delimiter_for(path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter, strict=True)
            header = next(reader, None)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise TableProofError(f"Cannot parse {path}: {exc}") from exc
    if header is None:
        raise TableProofError(f"Table is empty and has no header: {path}")
    _validate_header(path, header)
    return tuple(header)


def _validate_header(path: Path, header: list[str]) -> None:
    if not header:
        raise TableProofError(f"Table has an empty header: {path}")
    if any(name == "" for name in header):
        raise TableProofError(f"Table has a blank column name: {path}")
    repeated = sorted(name for name, count in Counter(header).items() if count > 1)
    if repeated:
        raise TableProofError(f"Table has duplicate column names {repeated}: {path}")


def read_table(path: Path, key_columns: tuple[str, ...]) -> TableData:
    """Parse a table without coercing or normalizing any field."""

    if not key_columns:
        raise TableProofError(f"At least one key column is required for {path}")
    delimiter = _delimiter_for(path)
    keys: Counter[Key] = Counter()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter, strict=True)
            header = next(reader, None)
            if header is None:
                raise TableProofError(f"Table is empty and has no header: {path}")
            _validate_header(path, header)
            missing = [name for name in key_columns if name not in header]
            if missing:
                raise TableProofError(f"Missing key columns {missing} in {path}")
            indexes = tuple(header.index(name) for name in key_columns)
            row_count = 0
            for line_number, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    raise TableProofError(
                        f"Row width mismatch in {path} at line {line_number}: "
                        f"expected {len(header)} fields, found {len(row)}"
                    )
                if row == header:
                    raise TableProofError(f"Repeated header row in {path} at line {line_number}")
                keys[tuple(row[index] for index in indexes)] += 1
                row_count += 1
    except TableProofError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise TableProofError(f"Cannot parse {path}: {exc}") from exc

    return TableData(
        path=path,
        sha256=_sha256(path),
        delimiter="tab" if delimiter == "\t" else "comma",
        header=tuple(header),
        row_count=row_count,
        key_columns=key_columns,
        keys=keys,
    )


def _key_sample(key: Key, show_raw: bool) -> str:
    if show_raw:
        return " | ".join(key)
    payload = "\x1f".join(key).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()[:16]}"


def _samples(keys: Iterable[Key], show_raw: bool, limit: int) -> list[str]:
    return [_key_sample(key, show_raw) for key in sorted(set(keys))[:limit]]


def _duplicate_stats(table: TableData, show_raw: bool, limit: int) -> dict[str, object]:
    duplicated = {key: count for key, count in table.usable_keys.items() if count > 1}
    return {
        "key_groups": len(duplicated),
        "rows_in_groups": sum(duplicated.values()),
        "excess_rows": sum(count - 1 for count in duplicated.values()),
        "examples": _samples(duplicated, show_raw, limit),
    }


def _observed_relationship(left: Counter[Key], right: Counter[Key]) -> str:
    if not left or not right:
        return "unknown"
    left_many = any(count > 1 for count in left.values())
    right_many = any(count > 1 for count in right.values())
    if left_many and right_many:
        return "many-to-many"
    if left_many:
        return "many-to-one"
    if right_many:
        return "one-to-many"
    return "one-to-one"


def _relationship_allowed(expected: str, observed: str) -> bool:
    if observed == "unknown":
        return False
    allowed = {
        "one-to-one": {"one-to-one"},
        "one-to-many": {"one-to-one", "one-to-many"},
        "many-to-one": {"one-to-one", "many-to-one"},
        "many-to-many": RELATIONSHIPS,
    }
    return observed in allowed[expected]


def _prediction_counts(left: TableData, right: TableData) -> dict[str, dict[str, float | int]]:
    left_keys = left.usable_keys
    right_keys = right.usable_keys
    common = left_keys.keys() & right_keys.keys()
    inner = sum(left_keys[key] * right_keys[key] for key in common)
    left_unmatched_rows = sum(count for key, count in left_keys.items() if key not in right_keys) + left.null_rows
    right_unmatched_rows = sum(count for key, count in right_keys.items() if key not in left_keys) + right.null_rows
    rows = {
        "inner": inner,
        "left": inner + left_unmatched_rows,
        "right": inner + right_unmatched_rows,
        "full": inner + left_unmatched_rows + right_unmatched_rows,
    }
    return {
        join_type: {
            "rows": count,
            "expansion_factor_vs_left": round(count / max(left.row_count, 1), 6),
            "expansion_factor_vs_larger_input": round(count / max(left.row_count, right.row_count, 1), 6),
        }
        for join_type, count in rows.items()
    }


def _canonical_whitespace(key: Key) -> Key:
    return tuple(part.strip() for part in key)


def _canonical_case(key: Key) -> Key:
    return tuple(part.casefold() for part in key)


def _strip_leading_zero(part: str) -> str:
    if not part.isascii() or not part.isdigit():
        return part
    stripped = part.lstrip("0")
    return stripped or "0"


def _canonical_zero(key: Key) -> Key:
    return tuple(_strip_leading_zero(part) for part in key)


def _normalization_hazard(
    left: Counter[Key],
    right: Counter[Key],
    canonicalize: Callable[[Key], Key],
    show_raw: bool,
    limit: int,
) -> dict[str, object]:
    left_groups: dict[Key, set[Key]] = defaultdict(set)
    right_groups: dict[Key, set[Key]] = defaultdict(set)
    for key in left:
        left_groups[canonicalize(key)].add(key)
    for key in right:
        right_groups[canonicalize(key)].add(key)
    collisions: list[Key] = []
    groups = 0
    for canonical in sorted(left_groups.keys() & right_groups.keys()):
        left_raw = left_groups[canonical]
        right_raw = right_groups[canonical]
        if any(lkey != rkey for lkey in left_raw for rkey in right_raw):
            groups += 1
            collisions.extend(sorted(left_raw | right_raw))
    return {
        "groups": groups,
        "examples": _samples(collisions, show_raw, limit),
    }


def _finding(code: str, severity: str, message: str, **context: object) -> dict[str, object]:
    return {"code": code, "severity": severity, "message": message, "context": context}


def _add_policy_finding(
    findings: list[dict[str, object]], code: str, policy: str, message: str, **context: object
) -> None:
    if policy != "ignore":
        findings.append(_finding(code, policy, message, **context))


def _table_report(table: TableData, show_raw: bool, limit: int) -> dict[str, object]:
    null_keys = [key for key in table.keys if any(part == "" for part in key)]
    return {
        "path": str(table.path),
        "sha256": table.sha256,
        "delimiter": table.delimiter,
        "rows": table.row_count,
        "columns": table.column_count,
        "key_columns": list(table.key_columns),
        "null_key_rows": table.null_rows,
        "null_key_examples": _samples(null_keys, show_raw, limit),
        "duplicates": _duplicate_stats(table, show_raw, limit),
    }


def _expected_result_counter(left: TableData, right: TableData, join_type: str) -> Counter[Key]:
    expected: Counter[Key] = Counter()
    left_usable = left.usable_keys
    right_usable = right.usable_keys
    common = left_usable.keys() & right_usable.keys()
    for key in common:
        expected[key] += left_usable[key] * right_usable[key]
    if join_type in {"left", "full"}:
        for key, count in left.keys.items():
            if any(part == "" for part in key) or key not in right_usable:
                expected[key] += count
    if join_type in {"right", "full"}:
        for key, count in right.keys.items():
            if any(part == "" for part in key) or key not in left_usable:
                expected[key] += count
    return expected


def _result_key_columns(spec: JoinSpec) -> tuple[str, ...]:
    if spec.result is None:
        raise AssertionError("result path is required")
    header = read_header(spec.result)
    if spec.result_keys:
        return spec.result_keys
    if all(key in header for key in spec.left_keys):
        return spec.left_keys
    if all(key in header for key in spec.right_keys):
        return spec.right_keys
    raise TableProofError(
        "Cannot infer result key columns. Set result_keys in TOML or pass --result-key explicitly."
    )


def _validate_result(
    spec: JoinSpec,
    left: TableData,
    right: TableData,
    findings: list[dict[str, object]],
) -> dict[str, object] | None:
    if spec.result is None:
        return None
    if spec.join_type not in JOIN_TYPES:
        raise TableProofError("join_type is required and must be inner, left, right, or full when result is set")
    result_keys = _result_key_columns(spec)
    if len(result_keys) != len(spec.left_keys):
        raise TableProofError("result_keys must have the same number of components as left_keys and right_keys")
    result = read_table(spec.result, result_keys)
    expected = _expected_result_counter(left, right, spec.join_type)
    missing = expected - result.keys
    excess = result.keys - expected
    expected_rows = sum(expected.values())
    missing_rows = sum(missing.values())
    excess_rows = sum(excess.values())
    if missing_rows or excess_rows:
        findings.append(
            _finding(
                "TP_RESULT_KEY_MULTISET_MISMATCH",
                "error",
                "The result key multiset does not match the declared join.",
                missing_rows=missing_rows,
                excess_rows=excess_rows,
                missing_examples=_samples(missing, spec.show_raw_keys, spec.sample_limit),
                excess_examples=_samples(excess, spec.show_raw_keys, spec.sample_limit),
            )
        )
    if result.row_count != expected_rows:
        findings.append(
            _finding(
                "TP_RESULT_ROW_COUNT_MISMATCH",
                "error",
                "The result row count differs from the declared join prediction.",
                expected_rows=expected_rows,
                actual_rows=result.row_count,
                delta=result.row_count - expected_rows,
            )
        )
    report = _table_report(result, spec.show_raw_keys, spec.sample_limit)
    report.update(
        {
            "join_type": spec.join_type,
            "expected_rows": expected_rows,
            "actual_rows": result.row_count,
            "row_delta": result.row_count - expected_rows,
            "missing_rows": missing_rows,
            "excess_rows": excess_rows,
            "missing_key_examples": _samples(missing, spec.show_raw_keys, spec.sample_limit),
            "excess_key_examples": _samples(excess, spec.show_raw_keys, spec.sample_limit),
        }
    )
    return report


def validate_spec(spec: JoinSpec) -> None:
    if len(spec.left_keys) != len(spec.right_keys):
        raise TableProofError("left_keys and right_keys must have the same number of components")
    if spec.relationship not in RELATIONSHIPS:
        raise TableProofError(f"Unsupported relationship: {spec.relationship}")
    for field_name, policy in {
        "left_unmatched": spec.left_unmatched,
        "right_unmatched": spec.right_unmatched,
        "null_keys": spec.null_keys,
    }.items():
        if policy not in POLICIES:
            raise TableProofError(f"{field_name} must be error, warn, or ignore")
    if spec.sample_limit < 0:
        raise TableProofError("sample_limit must be zero or greater")
    if spec.result is not None:
        if not isinstance(spec.join_type, str) or spec.join_type not in JOIN_TYPES:
            raise TableProofError("join_type is required when result is set")
    elif spec.join_type is not None:
        if not isinstance(spec.join_type, str) or spec.join_type not in JOIN_TYPES:
            raise TableProofError(f"Unsupported join_type: {spec.join_type}")
    if spec.result_keys is not None and spec.result is None:
        raise TableProofError("result_keys requires result")


def audit_join(spec: JoinSpec) -> dict[str, object]:
    """Audit one declared join and return a deterministic JSON-compatible report."""

    validate_spec(spec)
    left = read_table(spec.left, spec.left_keys)
    right = read_table(spec.right, spec.right_keys)
    findings: list[dict[str, object]] = []
    left_usable = left.usable_keys
    right_usable = right.usable_keys
    observed = _observed_relationship(left_usable, right_usable)

    if not _relationship_allowed(spec.relationship, observed):
        findings.append(
            _finding(
                "TP_RELATIONSHIP_VIOLATION",
                "error",
                "Observed key multiplicities violate the declared relationship constraint.",
                expected=spec.relationship,
                observed=observed,
            )
        )
    elif observed != spec.relationship:
        findings.append(
            _finding(
                "TP_RELATIONSHIP_NARROWER",
                "info",
                "Observed data is narrower than the allowed relationship constraint.",
                expected=spec.relationship,
                observed=observed,
            )
        )

    if left.null_rows:
        _add_policy_finding(
            findings,
            "TP_LEFT_NULL_KEY",
            spec.null_keys,
            "Left table contains blank key components.",
            rows=left.null_rows,
        )
    if right.null_rows:
        _add_policy_finding(
            findings,
            "TP_RIGHT_NULL_KEY",
            spec.null_keys,
            "Right table contains blank key components.",
            rows=right.null_rows,
        )

    left_orphan_keys = left_usable.keys() - right_usable.keys()
    right_orphan_keys = right_usable.keys() - left_usable.keys()
    left_orphan_rows = sum(left_usable[key] for key in left_orphan_keys)
    right_orphan_rows = sum(right_usable[key] for key in right_orphan_keys)
    if left_orphan_rows:
        _add_policy_finding(
            findings,
            "TP_LEFT_UNMATCHED",
            spec.left_unmatched,
            "Left table contains keys with no exact match on the right.",
            distinct_keys=len(left_orphan_keys),
            rows=left_orphan_rows,
            examples=_samples(left_orphan_keys, spec.show_raw_keys, spec.sample_limit),
        )
    if right_orphan_rows:
        _add_policy_finding(
            findings,
            "TP_RIGHT_UNMATCHED",
            spec.right_unmatched,
            "Right table contains keys with no exact match on the left.",
            distinct_keys=len(right_orphan_keys),
            rows=right_orphan_rows,
            examples=_samples(right_orphan_keys, spec.show_raw_keys, spec.sample_limit),
        )

    normalization = {}
    for name, code, canonicalizer in (
        ("whitespace", "TP_WHITESPACE_COLLISION", _canonical_whitespace),
        ("case", "TP_CASE_COLLISION", _canonical_case),
        ("leading_zero", "TP_LEADING_ZERO_COLLISION", _canonical_zero),
    ):
        hazard = _normalization_hazard(
            left_usable, right_usable, canonicalizer, spec.show_raw_keys, spec.sample_limit
        )
        normalization[name] = hazard
        if hazard["groups"]:
            findings.append(
                _finding(
                    code,
                    "warn",
                    f"Exact keys differ but would collide after {name.replace('_', ' ')} normalization.",
                    **hazard,
                )
            )

    predictions = _prediction_counts(left, right)
    many_many_keys = [
        key
        for key in left_usable.keys() & right_usable.keys()
        if left_usable[key] > 1 and right_usable[key] > 1
    ]
    if many_many_keys:
        findings.append(
            _finding(
                "TP_MANY_TO_MANY_EXPANSION",
                "warn" if spec.relationship == "many-to-many" else "error",
                "Matching keys repeat on both sides, so rows multiply within those key groups.",
                distinct_keys=len(many_many_keys),
                examples=_samples(many_many_keys, spec.show_raw_keys, spec.sample_limit),
                predicted_inner_rows=predictions["inner"]["rows"],
                expansion_factor_vs_larger_input=predictions["inner"]["expansion_factor_vs_larger_input"],
            )
        )

    result_report = _validate_result(spec, left, right, findings)
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warn" for item in findings)
    infos = sum(item["severity"] == "info" for item in findings)
    return {
        "name": spec.name,
        "keys": {"left": list(spec.left_keys), "right": list(spec.right_keys)},
        "expected_relationship": spec.relationship,
        "observed_relationship": observed,
        "left": _table_report(left, spec.show_raw_keys, spec.sample_limit),
        "right": _table_report(right, spec.show_raw_keys, spec.sample_limit),
        "unmatched": {
            "left_distinct_keys": len(left_orphan_keys),
            "left_rows": left_orphan_rows,
            "left_examples": _samples(left_orphan_keys, spec.show_raw_keys, spec.sample_limit),
            "right_distinct_keys": len(right_orphan_keys),
            "right_rows": right_orphan_rows,
            "right_examples": _samples(right_orphan_keys, spec.show_raw_keys, spec.sample_limit),
        },
        "normalization_hazards": normalization,
        "predictions": predictions,
        "selected_join_type": spec.join_type,
        "result": result_report,
        "findings": findings,
        "summary": {"errors": errors, "warnings": warnings, "infos": infos},
        "verdict": "fail" if errors else "pass",
    }


def audit_many(specs: Iterable[JoinSpec]) -> dict[str, object]:
    """Audit multiple joins and produce Report Schema v1."""

    audits = [audit_join(spec) for spec in specs]
    errors = sum(audit["summary"]["errors"] for audit in audits)  # type: ignore[index]
    warnings = sum(audit["summary"]["warnings"] for audit in audits)  # type: ignore[index]
    infos = sum(audit["summary"]["infos"] for audit in audits)  # type: ignore[index]
    return {
        "schema_version": "1.0",
        "tool": {"name": "tableproof", "version": __version__},
        "audits": audits,
        "summary": {"audits": len(audits), "errors": errors, "warnings": warnings, "infos": infos},
        "verdict": "fail" if errors else "pass",
    }
