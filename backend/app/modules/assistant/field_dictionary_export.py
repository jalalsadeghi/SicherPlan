"""CLI export for the packaged assistant field/lookup/platform-term corpus artifact."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    from app.modules.assistant.field_dictionary import export_field_lookup_corpus

    parser = argparse.ArgumentParser(description="Export the SicherPlan assistant field/lookup/platform-term corpus artifact.")
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to the full SicherPlan repository checkout.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the generated JSON artifact.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()

    summary = export_field_lookup_corpus(repo_root=repo_root, output_path=output_path)
    print(f"field_count={summary['field_count']}")
    print(f"lookup_count={summary['lookup_count']}")
    print(f"term_count={summary['term_count']}")
    print(f"field_counts_by_module={summary['field_counts_by_module']}")
    print(f"lookup_counts_by_module={summary['lookup_counts_by_module']}")
    print(f"term_counts_by_module={summary['term_counts_by_module']}")
    if summary["warnings"]:
        print(f"warnings={summary['warnings']}")
    else:
        print("warnings=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
