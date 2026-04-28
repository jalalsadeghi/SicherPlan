from __future__ import annotations

from pathlib import Path

from tests.modules.assistant.golden_qa_support import (
    load_field_lookup_golden_cases,
    render_result_row,
    run_case,
)


def test_golden_fields_lookups(tmp_path: Path) -> None:
    cases = load_field_lookup_golden_cases()
    results = [run_case(tmp_path / case.id, case) for case in cases]

    print("Question | Intent | Top sources | Content-bearing count | Source basis | Pass/Fail")
    for result in results:
        print(render_result_row(result))

    failures = [result for result in results if not result.passed]
    assert not failures, {
        result.case.id: result.failures
        for result in failures
    }
