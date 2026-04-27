from __future__ import annotations

from app.modules.assistant.schemas import AssistantNavigationLink
from app.modules.assistant.service import AssistantService


def test_normalize_user_facing_answer_links_removes_page_code_suffix_and_builds_inline_link_segments() -> None:
    service = AssistantService.__new__(AssistantService)

    answer, segments = service._normalize_user_facing_answer_links(
        answer_text="Dies können Sie im Mitarbeiter-Workspace (E-01) überprüfen.",
        allowed_links=[
            AssistantNavigationLink(
                label="Mitarbeiter-Workspace",
                path="/admin/employees",
                page_id="E-01",
            ).model_dump(mode="json")
        ],
    )

    assert answer == "Dies können Sie im Mitarbeiter-Workspace überprüfen."
    assert [segment.type for segment in segments] == ["text", "link", "text"]
    assert segments[1].text == "Mitarbeiter-Workspace"
    assert segments[1].link is not None
    assert segments[1].link.path == "/admin/employees"
    assert "(E-01)" not in answer


def test_normalize_user_facing_answer_links_replaces_bare_page_id_with_plain_label_when_no_allowed_link_exists() -> None:
    service = AssistantService.__new__(AssistantService)

    answer, segments = service._normalize_user_facing_answer_links(
        answer_text="Dies erfolgt auf P-03.",
        allowed_links=[],
    )

    assert answer == "Dies erfolgt auf Shift Planning."
    assert [segment.type for segment in segments] == ["text"]
    assert "P-03" not in answer


def test_normalize_user_facing_answer_links_preserves_existing_human_label_as_inline_link_alias() -> None:
    service = AssistantService.__new__(AssistantService)

    answer, segments = service._normalize_user_facing_answer_links(
        answer_text="Dies erfolgt auf Schichtplanung (P-03).",
        allowed_links=[
            AssistantNavigationLink(
                label="Shift Planning",
                path="/admin/planning-shifts",
                page_id="P-03",
            ).model_dump(mode="json")
        ],
    )

    assert answer == "Dies erfolgt auf Schichtplanung."
    assert [segment.type for segment in segments] == ["text", "link", "text"]
    assert segments[1].text == "Schichtplanung"
    assert segments[1].link is not None
    assert segments[1].link.path == "/admin/planning-shifts"
