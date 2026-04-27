from __future__ import annotations

import json
from types import SimpleNamespace

from app.modules.assistant.service import AssistantService


def test_tool_result_summary_compacts_planning_match_records() -> None:
    raw_matches = [
        {
            "assignment_ref": f"asg-{index}",
            "assignment_status": "assigned",
            "release_state": "released",
            "is_visible_candidate_for_employee_app": True,
            "notes": "x" * 400,
            "nested": {"foo": "bar", "debug": "y" * 300},
        }
        for index in range(8)
    ]
    result = SimpleNamespace(
        tool_name="planning.find_assignments",
        ok=True,
        redacted_output={
            "matches": raw_matches,
            "match_count": len(raw_matches),
            "truncated": True,
            "missing_permissions": [{"permission": "planning.read", "reason": "Need planning read."}],
        },
        data=None,
        error_code=None,
        error_message=None,
        missing_permissions=[],
        entity_refs={"employee_ref": "EMP-1", "shift_ref": "SHIFT-1"},
    )

    summary = AssistantService._tool_result_to_summary(result)  # noqa: SLF001
    payload = summary.summary

    assert payload["ok"] is True
    assert payload["summary"]["counts"]["match_count"] == 8
    assert payload["summary"]["counts"]["truncated"] is True
    assert payload["summary"]["entity_refs"] == ["employee_ref:EMP-1", "shift_ref:SHIFT-1"]
    assert payload["summary"]["missing_permissions"] == [
        {"permission": "planning.read", "reason": "Need planning read."}
    ]
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert '"matches"' not in serialized
    assert '"nested"' not in serialized
    assert "notes" not in serialized
    assert "asg-0" in serialized


def test_tool_result_provider_output_uses_compact_summary_shape() -> None:
    result = SimpleNamespace(
        tool_name="assistant.search_accessible_pages",
        ok=True,
        redacted_output={
            "pages": [
                {"page_id": "C-01", "label": "Customers Workspace", "path": "/admin/customers"},
                {"page_id": "P-02", "label": "Orders and Planning", "path": "/admin/planning"},
            ],
            "truncated": False,
        },
        data=None,
        error_code=None,
        error_message=None,
        missing_permissions=[],
        entity_refs=None,
    )

    output = AssistantService._tool_result_to_provider_output(  # noqa: SLF001
        requested_call={"call_id": "call-1"},
        tool_result=result,
    )
    payload = json.loads(output["output"])

    assert output["call_id"] == "call-1"
    assert payload["summary"]["counts"]["page_count"] == 2
    assert '"pages"' not in output["output"]
    assert "Customers Workspace" in output["output"]
