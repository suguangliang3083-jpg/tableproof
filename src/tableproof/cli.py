"""Command-line interface for TableProof."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .audit import audit_many
from .config import CONFIG_TEMPLATE, load_config
from .models import JoinSpec, TableProofError
from .render import github_annotations, render

EXIT_OK = 0
EXIT_POLICY = 1
EXIT_USAGE = 2


def _split_keys(values: list[str] | None, option: str) -> tuple[str, ...]:
    if not values:
        raise TableProofError(f"{option} is required")
    keys: list[str] = []
    for value in values:
        keys.extend(part for part in value.split(",") if part)
    if not keys:
        raise TableProofError(f"{option} must contain a non-empty column name")
    return tuple(keys)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tableproof",
        description="Audit CSV/TSV join cardinality and materialized result integrity.",
    )
    parser.add_argument("--version", action="version", version=f"tableproof {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="write an annotated tableproof.toml")
    init_parser.add_argument("--path", type=Path, default=Path("tableproof.toml"))
    init_parser.add_argument("--force", action="store_true", help="overwrite an existing file")

    check = subparsers.add_parser("check", help="audit one join or a TOML configuration")
    source = check.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", type=Path, help="v1 TOML configuration")
    source.add_argument("--left", type=Path, help="left CSV or TSV")
    check.add_argument("--right", type=Path)
    check.add_argument("--left-key", action="append", help="repeat or comma-separate composite keys")
    check.add_argument("--right-key", action="append", help="repeat or comma-separate composite keys")
    check.add_argument("--expect", choices=sorted({"one-to-one", "one-to-many", "many-to-one", "many-to-many"}))
    check.add_argument("--left-unmatched", choices=("error", "warn", "ignore"), default="warn")
    check.add_argument("--right-unmatched", choices=("error", "warn", "ignore"), default="warn")
    check.add_argument("--null-keys", choices=("error", "warn", "ignore"), default="error")
    check.add_argument("--result", type=Path)
    check.add_argument("--result-key", action="append")
    check.add_argument("--join-type", choices=("inner", "left", "right", "full"))
    check.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    check.add_argument("--output", type=Path)
    check.add_argument("--show-raw-keys", action="store_true", help="include raw example keys in the report")
    check.add_argument("--sample-limit", type=int, default=5)
    check.add_argument("--fail-on", choices=("error", "warning"))
    check.add_argument("--github-annotations", action="store_true", help=argparse.SUPPRESS)
    return parser


def _direct_spec(args: argparse.Namespace) -> JoinSpec:
    if args.right is None or args.expect is None:
        raise TableProofError("--right and --expect are required in direct mode")
    left_keys = _split_keys(args.left_key, "--left-key")
    right_keys = _split_keys(args.right_key, "--right-key")
    result_keys = _split_keys(args.result_key, "--result-key") if args.result_key else None
    return JoinSpec(
        name=f"{args.left.name}-to-{args.right.name}",
        left=args.left.resolve(),
        right=args.right.resolve(),
        left_keys=left_keys,
        right_keys=right_keys,
        relationship=args.expect,
        left_unmatched=args.left_unmatched,
        right_unmatched=args.right_unmatched,
        null_keys=args.null_keys,
        result=args.result.resolve() if args.result else None,
        join_type=args.join_type,
        result_keys=result_keys,
        show_raw_keys=args.show_raw_keys,
        sample_limit=args.sample_limit,
    )


def _run_init(args: argparse.Namespace) -> int:
    path: Path = args.path
    if path.exists() and not args.force:
        raise TableProofError(f"Refusing to overwrite existing file: {path} (use --force)")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(CONFIG_TEMPLATE, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise TableProofError(f"Cannot write {path}: {exc}") from exc
    print(f"Wrote {path}")
    return EXIT_OK


def _run_check(args: argparse.Namespace) -> int:
    if args.config:
        override = True if args.show_raw_keys else None
        specs, configured_fail_on = load_config(args.config, show_raw_override=override)
    else:
        specs = [_direct_spec(args)]
        configured_fail_on = "error"
    report = audit_many(specs)
    rendered = render(report, args.format)
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        except OSError as exc:
            raise TableProofError(f"Cannot write report {args.output}: {exc}") from exc
    else:
        sys.stdout.write(rendered)
    if args.github_annotations:
        for annotation in github_annotations(report):
            print(annotation, file=sys.stderr)
    fail_on = args.fail_on or configured_fail_on
    if report["summary"]["errors"]:
        return EXIT_POLICY
    if fail_on == "warning" and report["summary"]["warnings"]:
        return EXIT_POLICY
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "init":
            return _run_init(args)
        return _run_check(args)
    except TableProofError as exc:
        print(f"tableproof: error: {exc}", file=sys.stderr)
        return EXIT_USAGE
