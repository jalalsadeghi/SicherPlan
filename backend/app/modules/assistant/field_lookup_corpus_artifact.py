"""Helper CLI for deterministic generation and freshness checks of the field/lookup corpus artifact."""

from __future__ import annotations

import argparse
import filecmp
import tempfile
from pathlib import Path
from typing import Sequence

from app.modules.assistant.field_dictionary import export_field_lookup_corpus

_ARTIFACT_PATH = Path("backend/app/modules/assistant/generated/field_lookup_corpus.json")


def _resolve_repo_root(repo_root: str) -> Path:
    return Path(repo_root).resolve()


def _resolve_output_path(output: str, *, cwd: Path) -> Path:
    path = Path(output)
    if not path.is_absolute():
        path = (cwd / path).resolve()
    return path


def _artifact_path(repo_root: Path) -> Path:
    return repo_root / _ARTIFACT_PATH


def _print_summary(summary: dict[str, object]) -> None:
    print(f"field_count={summary['field_count']}")
    print(f"lookup_count={summary['lookup_count']}")
    print(f"term_count={summary['term_count']}")
    print(f"field_counts_by_module={summary['field_counts_by_module']}")
    print(f"lookup_counts_by_module={summary['lookup_counts_by_module']}")
    print(f"term_counts_by_module={summary['term_counts_by_module']}")
    warnings = summary["warnings"]
    print(f"warnings={warnings if warnings else []}")


def generate_artifact(*, repo_root: Path, output_path: Path) -> dict[str, object]:
    summary = export_field_lookup_corpus(repo_root=repo_root, output_path=output_path)
    _print_summary(summary)
    print(f"artifact={output_path.relative_to(repo_root) if output_path.is_relative_to(repo_root) else output_path.name}")
    return summary


def check_deterministic(*, repo_root: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="field-lookup-corpus-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        first_output = temp_dir / "first.json"
        second_output = temp_dir / "second.json"
        export_field_lookup_corpus(repo_root=repo_root, output_path=first_output)
        export_field_lookup_corpus(repo_root=repo_root, output_path=second_output)
        if not filecmp.cmp(first_output, second_output, shallow=False):
            print("Field/lookup corpus export is nondeterministic.")
            return 1
    print("Field/lookup corpus export is deterministic.")
    return 0


def check_committed(*, repo_root: Path) -> int:
    committed_artifact = _artifact_path(repo_root)
    with tempfile.TemporaryDirectory(prefix="field-lookup-corpus-") as temp_dir_name:
        temp_output = Path(temp_dir_name) / "fresh.json"
        export_field_lookup_corpus(repo_root=repo_root, output_path=temp_output)
        if not committed_artifact.is_file():
            print(f"Committed artifact missing: {_ARTIFACT_PATH.as_posix()}")
            return 1
        if not filecmp.cmp(committed_artifact, temp_output, shallow=False):
            print(f"Committed artifact is stale: {_ARTIFACT_PATH.as_posix()}")
            return 1
    print("Committed field/lookup corpus artifact is current.")
    return 0


def ensure_current(*, repo_root: Path) -> int:
    deterministic_result = check_deterministic(repo_root=repo_root)
    if deterministic_result != 0:
        return deterministic_result
    committed_artifact = _artifact_path(repo_root)
    summary = export_field_lookup_corpus(repo_root=repo_root, output_path=committed_artifact)
    _print_summary(summary)
    print(f"Updated {_ARTIFACT_PATH.as_posix()}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the assistant field/lookup corpus artifact.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate the corpus artifact at a chosen output path.")
    generate_parser.add_argument("--repo-root", required=True, help="Path to the full SicherPlan repository checkout.")
    generate_parser.add_argument("--output", required=True, help="Output path for the generated corpus JSON.")

    deterministic_parser = subparsers.add_parser("check-deterministic", help="Export twice and fail if the output differs.")
    deterministic_parser.add_argument("--repo-root", required=True, help="Path to the full SicherPlan repository checkout.")

    committed_parser = subparsers.add_parser("check-committed", help="Compare the committed artifact against fresh generated output.")
    committed_parser.add_argument("--repo-root", required=True, help="Path to the full SicherPlan repository checkout.")

    ensure_parser = subparsers.add_parser("ensure-current", help="Verify determinism and then update the committed artifact in place.")
    ensure_parser.add_argument("--repo-root", required=True, help="Path to the full SicherPlan repository checkout.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        repo_root = _resolve_repo_root(args.repo_root)
        output_path = _resolve_output_path(args.output, cwd=Path.cwd())
        generate_artifact(repo_root=repo_root, output_path=output_path)
        return 0
    if args.command == "check-deterministic":
        return check_deterministic(repo_root=_resolve_repo_root(args.repo_root))
    if args.command == "check-committed":
        return check_committed(repo_root=_resolve_repo_root(args.repo_root))
    if args.command == "ensure-current":
        return ensure_current(repo_root=_resolve_repo_root(args.repo_root))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
