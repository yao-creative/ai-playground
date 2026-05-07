import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
PLANNING06_DIR = SRC_DIR / "06-agentic-planning"

for path in (PLANNING06_DIR, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


orchestrator_module = load_module("agentic_planning_orchestrator", PLANNING06_DIR / "orchestrator.py")
main_module = load_module("agentic_planning_main", PLANNING06_DIR / "main.py")
models_module = load_module("agentic_planning_models", PLANNING06_DIR / "models.py")
planning_data_module = load_module("agentic_planning_data", PLANNING06_DIR / "data.py")
planning_retrieval_module = load_module("agentic_planning_retrieval", PLANNING06_DIR / "retrieval.py")
terminal_app_module = load_module("agentic_planning_terminal_app", PLANNING06_DIR / "terminal_app.py")


class FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class FakeResponsesAPI:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, str]] = []

    def create(self, *, model: str, input: str, stream: bool = False):
        self.calls.append({"model": model, "input": input, "stream": str(stream)})
        if not self.outputs:
            raise AssertionError("No fake response configured for this step.")
        output = self.outputs.pop(0)
        return FakeResponse(output)


class FakeClient:
    def __init__(self, outputs: list[str]) -> None:
        self.responses = FakeResponsesAPI(outputs)


def build_chatbot(outputs: list[str]):
    client = FakeClient(outputs=outputs)
    chatbot = orchestrator_module.AgenticPlanningOrchestrator(
        client=client,
        model="gpt-5-mini",
        documents=planning_data_module.build_documents(),
        retrieval_strategy=planning_retrieval_module.KeywordRetrievalStrategy(
            planning_retrieval_module.TiktokenTokenizer("gpt-5-mini")
        ),
    )
    return client, chatbot


def test_prepare_plan_then_accept_executes_answer() -> None:
    client, chatbot = build_chatbot(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"remote work days per week","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer remote work policy question","evidence_needed":["remote days"],"proposed_actions":["cite policy"]}',
            '{"answer":"Employees may work remotely up to three days per week with manager approval.","cited_doc_ids":["doc-001"],"supported":true}',
        ]
    )

    session = chatbot.prepare_plan("How many remote days are allowed?")

    assert session.__class__.__name__ == "PlanningSession"
    assert session.plan.objective == "Answer remote work policy question"
    result = chatbot.execute_accepted_plan(session)

    assert result.supported is True
    assert result.cited_doc_ids == ["doc-001"]
    assert "three days per week" in result.final_answer
    assert len(result.steps) == 1
    assert client.responses.outputs == []


def test_redraft_plan_uses_feedback_without_recollecting_evidence() -> None:
    client, chatbot = build_chatbot(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"remote work days per week","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer remote work policy question","evidence_needed":["remote days"],"proposed_actions":["summarize policy"]}',
            '{"objective":"Answer remote work policy question precisely","evidence_needed":["remote day count"],"proposed_actions":["cite exact limit"]}',
        ]
    )

    session = chatbot.prepare_plan("How many remote days are allowed?")
    assert session.__class__.__name__ == "PlanningSession"

    revised = chatbot.redraft_plan(session, "Make the plan more explicit about the exact day count.")

    assert revised.revision_count == 1
    assert revised.steps == session.steps
    assert revised.evidence_summary == session.evidence_summary
    assert revised.plan.proposed_actions == ["cite exact limit"]
    assert len(client.responses.calls) == 4


def test_execute_accepted_plan_enforces_supported_requires_citations() -> None:
    _, chatbot = build_chatbot(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"data retention logs","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer retention period","evidence_needed":["log retention"],"proposed_actions":["state exact retention"]}',
            '{"answer":"Application logs are retained for 90 days.","cited_doc_ids":[],"supported":true}',
        ]
    )

    session = chatbot.prepare_plan("How long are application logs retained?")
    assert session.__class__.__name__ == "PlanningSession"

    result = chatbot.execute_accepted_plan(session)

    assert result.supported is False
    assert result.cited_doc_ids == []
    assert "90 days" in result.final_answer


def test_prepare_plan_returns_safe_fallback_when_evidence_collection_blocks() -> None:
    _, chatbot = build_chatbot(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"gym reimbursement","limit":2}}',
            'Action: {"tool_name":"search_documents","arguments":{"query":"gym reimbursement","limit":2}}',
        ]
    )

    result = chatbot.prepare_plan("Do we reimburse gym memberships?")

    assert result.__class__.__name__ == "AgentRunResult"
    assert result.supported is False
    assert result.final_answer == "I do not have enough supported evidence to answer confidently."


def test_terminal_app_routes_accept_redraft_and_exit() -> None:
    _, chatbot = build_chatbot(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"remote work days per week","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer remote work policy question","evidence_needed":["remote days"],"proposed_actions":["summarize policy"]}',
            '{"objective":"Answer remote work policy question precisely","evidence_needed":["remote day count"],"proposed_actions":["cite exact limit"]}',
            '{"answer":"Employees may work remotely up to three days per week with manager approval.","cited_doc_ids":["doc-001"],"supported":true}',
            'Action: {"tool_name":"search_documents","arguments":{"query":"office access hours","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer office access question","evidence_needed":["office hours"],"proposed_actions":["cite hours"]}',
        ]
    )
    app = terminal_app_module.TerminalChatApp(chatbot)

    plan_1 = app.handle_input("How many remote days are allowed?")
    assert "Plan Spec:" in plan_1
    assert "Options:" in plan_1
    assert app.active_session is not None

    invalid_choice = app.handle_input("Make it more explicit about the exact day count.")
    assert invalid_choice == "Choose one option: accept, redraft, or exit plan."
    assert app.awaiting_redraft_feedback is False
    assert app.active_session is not None

    redraft_prompt = app.handle_input("redraft")
    assert redraft_prompt == "Redraft selected. Reply with the plan changes you want."
    assert app.awaiting_redraft_feedback is True

    plan_2 = app.handle_input("Make it more explicit about the exact day count.")
    assert "Revision: 1" in plan_2
    assert "cite exact limit" in plan_2
    assert app.awaiting_redraft_feedback is False
    assert app.active_session is not None

    answer = app.handle_input("accept")
    assert "three days per week" in answer
    assert "Sources: doc-001" in answer
    assert app.active_session is None
    assert app.awaiting_redraft_feedback is False

    plan_3 = app.handle_input("What time can employees access the office?")
    assert "Plan Spec:" in plan_3
    assert app.active_session is not None

    exit_message = app.handle_input("exit plan")
    assert exit_message == "Plan loop exited. No answer drafted for this turn."
    assert app.active_session is None
    assert app.awaiting_redraft_feedback is False


def test_build_app_accepts_max_steps_only(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")

    class StubOpenAI:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    monkeypatch.setattr(main_module, "OpenAI", StubOpenAI)

    app = main_module.build_app(strategy="keyword", max_steps=3)
    assert app is not None
