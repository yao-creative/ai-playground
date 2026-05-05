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



def test_agentic_planning_happy_path_with_one_redraft() -> None:
    client = FakeClient(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"remote work days per week","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer remote work policy question","evidence_needed":["remote days"],"proposed_actions":["cite policy"]}',
            '{"answer":"Employees may work remotely with manager approval.","cited_doc_ids":["doc-001"],"supported":true}',
            '{"pass_review":false,"issues":["Missing exact day count"],"revision_instructions":"Include numeric day limit from doc-001."}',
            '{"answer":"Employees may work remotely up to three days per week with manager approval.","cited_doc_ids":["doc-001"],"supported":true}',
            '{"pass_review":true,"issues":[],"revision_instructions":""}',
        ]
    )
    chatbot = orchestrator_module.AgenticPlanningOrchestrator(
        client=client,
        model="gpt-5-mini",
        documents=planning_data_module.build_documents(),
        retrieval_strategy=planning_retrieval_module.KeywordRetrievalStrategy(
            planning_retrieval_module.TiktokenTokenizer("gpt-5-mini")
        ),
        revision_config=models_module.RevisionConfig(max_redrafts=1),
    )

    result = chatbot.answer("How many remote days are allowed?")

    assert result.supported is True
    assert result.cited_doc_ids == ["doc-001"]
    assert "three days per week" in result.final_answer
    assert len(result.steps) == 1
    assert result.review is not None and result.review.pass_review is True



def test_agentic_planning_returns_safe_fallback_when_review_fails_after_redraft() -> None:
    client = FakeClient(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"gym reimbursement","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer reimbursement question","evidence_needed":["policy mention"],"proposed_actions":["state unsupported if absent"]}',
            '{"answer":"We reimburse gym memberships.","cited_doc_ids":["doc-003"],"supported":true}',
            '{"pass_review":false,"issues":["Claim unsupported by evidence"],"revision_instructions":"Remove unsupported claim."}',
            '{"answer":"Gym reimbursement is available.","cited_doc_ids":["doc-003"],"supported":true}',
            '{"pass_review":false,"issues":["Still unsupported"],"revision_instructions":""}',
        ]
    )
    chatbot = orchestrator_module.AgenticPlanningOrchestrator(
        client=client,
        model="gpt-5-mini",
        documents=planning_data_module.build_documents(),
        retrieval_strategy=planning_retrieval_module.KeywordRetrievalStrategy(
            planning_retrieval_module.TiktokenTokenizer("gpt-5-mini")
        ),
        revision_config=models_module.RevisionConfig(max_redrafts=1),
    )

    result = chatbot.answer("Do we reimburse gym memberships?")

    assert result.supported is False
    assert result.cited_doc_ids == []
    assert result.final_answer == "I do not have enough supported evidence to answer confidently."



def test_agentic_planning_respects_zero_redraft_budget() -> None:
    client = FakeClient(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"office access hours","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer access hours","evidence_needed":["office window"],"proposed_actions":["cite doc"]}',
            '{"answer":"Office access is available.","cited_doc_ids":["doc-010"],"supported":true}',
            '{"pass_review":false,"issues":["Missing exact hours"],"revision_instructions":"Include exact hours."}',
        ]
    )
    chatbot = orchestrator_module.AgenticPlanningOrchestrator(
        client=client,
        model="gpt-5-mini",
        documents=planning_data_module.build_documents(),
        retrieval_strategy=planning_retrieval_module.KeywordRetrievalStrategy(
            planning_retrieval_module.TiktokenTokenizer("gpt-5-mini")
        ),
        revision_config=models_module.RevisionConfig(max_redrafts=0),
    )

    result = chatbot.answer("What time can employees access the office?")

    assert result.supported is False
    assert result.final_answer == "I do not have enough supported evidence to answer confidently."
    assert client.responses.outputs == []



def test_agentic_planning_enforces_supported_requires_citations() -> None:
    client = FakeClient(
        outputs=[
            'Action: {"tool_name":"search_documents","arguments":{"query":"data retention logs","limit":2}}',
            'Stop: {"reason":"enough evidence"}',
            '{"objective":"Answer retention period","evidence_needed":["log retention"],"proposed_actions":["state exact retention"]}',
            '{"answer":"Application logs are retained for 90 days.","cited_doc_ids":[],"supported":true}',
            '{"pass_review":true,"issues":[],"revision_instructions":""}',
        ]
    )
    chatbot = orchestrator_module.AgenticPlanningOrchestrator(
        client=client,
        model="gpt-5-mini",
        documents=planning_data_module.build_documents(),
        retrieval_strategy=planning_retrieval_module.KeywordRetrievalStrategy(
            planning_retrieval_module.TiktokenTokenizer("gpt-5-mini")
        ),
        revision_config=models_module.RevisionConfig(max_redrafts=1),
    )

    result = chatbot.answer("How long are application logs retained?")

    assert result.supported is False
    assert result.cited_doc_ids == []
    assert "90 days" in result.final_answer



def test_build_app_accepts_max_redrafts(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")

    class StubOpenAI:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    monkeypatch.setattr(main_module, "OpenAI", StubOpenAI)

    app = main_module.build_app(strategy="keyword", max_steps=3, max_redrafts=1)
    assert app is not None
