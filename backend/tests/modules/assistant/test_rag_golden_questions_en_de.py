from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context, _repository, _service


@dataclass
class _GoldenProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)
    call_count: int = 0

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        self.call_count += 1
        intent = str((request.grounding_context or {}).get("retrieval_plan", {}).get("workflow_intent") or "")
        language = request.response_language
        if language == "de":
            answer = {
                "contract_or_document_register": "Verifizierte Hinweise zeigen auf Platform Services sowie auf Kunden- und Auftragskontext. Ein eigenständiger Vertragsbereich ist nicht verifiziert.",
                "customer_create": "Erstellen Sie den Kunden im Kundenkontext. Die verifizierten Quellen verweisen auf den Kundenarbeitsbereich.",
                "customer_order_create": "Starten Sie im Kunden- und Auftragskontext. Die verifizierten Quellen verweisen auf Kunden und Orders & Planning Records.",
                "employee_assign_to_shift": "Prüfen Sie zuerst den Mitarbeitendenkontext und gehen Sie dann in Shift Planning und Staffing Board.",
                "shift_release_to_employee_app": "Die Freigabe läuft über den Planungs- und Sichtbarkeitskontext für die Mitarbeiter-App.",
            }[intent]
        else:
            answer = {
                "contract_or_document_register": "Verified guidance points to Platform Services plus customer and order context. A standalone contract workflow is not verified.",
                "customer_create": "Create the customer in the customer workspace. The verified sources point to the customer context.",
                "customer_order_create": "Start in the customer and order context. Verified sources point to Customers and Orders & Planning Records.",
                "employee_assign_to_shift": "Check the employee context first, then continue into Shift Planning and the Staffing Board.",
                "shift_release_to_employee_app": "The release flow goes through planning and released-visibility context for the employee app.",
            }[intent]
        return AssistantProviderResult(
            final_response={
                "answer": answer,
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=answer,
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def test_golden_questions_en_de_emit_grounded_answers_and_source_basis() -> None:
    cases = [
        ("Wie registriere ich einen neuen Vertrag?", "de", "contract_or_document_register"),
        ("How do I register a new contract?", "en", "contract_or_document_register"),
        ("How do I create a new customer?", "en", "customer_create"),
        ("Wie erstelle ich einen neuen Kunden?", "de", "customer_create"),
        ("How do I create a new order for a customer?", "en", "customer_order_create"),
        ("Wie erstelle ich einen neuen Auftrag für einen Kunden?", "de", "customer_order_create"),
        ("How do I assign an employee to a shift?", "en", "employee_assign_to_shift"),
        ("Wie weise ich einen Mitarbeiter einer Schicht zu?", "de", "employee_assign_to_shift"),
        ("How do I release a shift to the employee app?", "en", "shift_release_to_employee_app"),
        ("Wie gebe ich eine Schicht für die Mitarbeiter-App frei?", "de", "shift_release_to_employee_app"),
    ]
    permissions = (
        "assistant.chat.access",
        "customers.customer.read",
        "employees.employee.read",
        "employees.employee.write",
        "planning.order.read",
        "planning.record.read",
        "planning.shift.read",
        "planning.staffing.read",
    )

    provider = _GoldenProvider()
    print("Question | Detected intent | Top sources | Content-bearing count | Provider called | Source basis | Pass/Fail")
    for question, language, expected_intent in cases:
        repository = _repository()
        conversation = repository.create_conversation(
            tenant_id="tenant-1",
            user_id="assistant-user-1",
            title=None,
            locale=language,
            last_route_name=None,
            last_route_path=None,
        )
        response = _service(repository, provider, provider_mode="openai").add_message(
            conversation.id,
            AssistantMessageCreate(message=question),
            _context(*permissions),
        )
        request = provider.requests[-1]
        rag_trace = response.rag_trace
        assert rag_trace is not None
        assert request.grounding_context is not None
        assert request.grounding_context["retrieval_plan"]["workflow_intent"] == expected_intent
        assert rag_trace.content_bearing_source_count > 0
        assert response.response_language == language
        assert response.source_basis
        assert response.confidence in {"medium", "high"}
        assert "look around these workspaces" not in response.answer.casefold()
        assert "contract page" not in response.answer.casefold()
        top_sources = ",".join(
            filter(None, [item.page_id or item.source_name for item in response.source_basis[:3]])
        )
        print(
            f"{question} | {expected_intent} | {top_sources} | "
            f"{rag_trace.content_bearing_source_count} | yes | yes | PASS"
        )
