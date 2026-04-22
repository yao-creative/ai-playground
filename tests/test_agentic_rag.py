import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
RAG03_DIR = SRC_DIR / "03-rag-chat"
RAG05_DIR = SRC_DIR / "05-agentic-rag"

for path in (RAG05_DIR, RAG03_DIR, SRC_DIR):
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


agent_module = load_module("agentic_rag_agent", RAG05_DIR / "agent.py")
main_module = load_module("agentic_rag_main", RAG05_DIR / "main.py")
terminal_module = load_module("agentic_rag_terminal", RAG05_DIR / "terminal_app.py")

from data import build_documents
from retrieval import KeywordRetrievalStrategy


class FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class FakeResponsesAPI:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, str]] = []

    def create(self, *, model: str, input: str):
        self.calls.append({"model": model, "input": input})
        if not self.outputs:
            raise AssertionError("No fake response configured for this step.")
        return FakeResponse(self.outputs.pop(0))


class FakeClient:
    def __init__(self, outputs: list[str]) -> None:
        self.responses = FakeResponsesAPI(outputs)


class StubAgent:
    def __init__(self, answers) -> None:
        self.answers = list(answers)
        self.calls: list[tuple[str, list[tuple[str, str]]]] = []

    def answer(self, user_input: str, chat_history):
        self.calls.append((user_input, list(chat_history)))
        return self.answers.pop(0)


def test_agentic_rag_answers_with_citations() -> None:
    client = FakeClient(
        outputs=[
            '{"tool_name":"search_documents","arguments":{"query":"remote work days per week","limit":2}}',
            '{"tool_name":"finish","arguments":{"answer":"Employees may work remotely up to three days per week with manager approval.","cited_doc_ids":["doc-001"],"supported":true}}',
        ]
    )
    chatbot = agent_module.AgenticRAG(
        client=client,
        model="gpt-5-mini",
        documents=build_documents(),
        retrieval_strategy=KeywordRetrievalStrategy(main_module.TiktokenTokenizer("gpt-5-mini")),
    )

    result = chatbot.answer("How many remote days are allowed?")

    assert result.supported is True
    assert result.cited_doc_ids == ["doc-001"]
    assert "three days per week" in result.final_answer
    assert [step.tool_call.tool_name for step in result.steps] == ["search_documents"]


def test_agentic_rag_returns_unsupported_when_finish_lacks_citations() -> None:
    client = FakeClient(
        outputs=[
            '{"tool_name":"search_documents","arguments":{"query":"gym reimbursement","limit":2}}',
            '{"tool_name":"finish","arguments":{"answer":"The docs do not mention gym reimbursement.","cited_doc_ids":[],"supported":true}}',
        ]
    )
    chatbot = agent_module.AgenticRAG(
        client=client,
        model="gpt-5-mini",
        documents=build_documents(),
        retrieval_strategy=KeywordRetrievalStrategy(main_module.TiktokenTokenizer("gpt-5-mini")),
    )

    result = chatbot.answer("Do we reimburse gym memberships?")

    assert result.supported is False
    assert result.cited_doc_ids == []
    assert result.final_answer == "The docs do not mention gym reimbursement."


def test_agentic_rag_stops_on_duplicate_tool_calls() -> None:
    client = FakeClient(
        outputs=[
            '{"tool_name":"search_documents","arguments":{"query":"office access hours","limit":2}}',
            '{"tool_name":"search_documents","arguments":{"query":"office access hours","limit":2}}',
        ]
    )
    chatbot = agent_module.AgenticRAG(
        client=client,
        model="gpt-5-mini",
        documents=build_documents(),
        retrieval_strategy=KeywordRetrievalStrategy(main_module.TiktokenTokenizer("gpt-5-mini")),
    )

    result = chatbot.answer("What time can employees access the office?")

    assert result.supported is False
    assert "enough new evidence" in result.final_answer.lower()
    assert len(result.steps) == 1


def test_terminal_app_prints_sources_for_supported_answers(capsys, monkeypatch) -> None:
    answer = agent_module.AgentRunResult(
        final_answer="Employees may access the office from 07:00 to 22:00 using their badge.",
        cited_doc_ids=["doc-010"],
        supported=True,
        steps=[],
    )
    stub_agent = StubAgent([answer])
    app = terminal_module.TerminalChatApp(stub_agent)
    inputs = iter(["When is the office open?", "bye"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    app.run()

    output = capsys.readouterr().out
    assert "AI: Hello! Type 'bye' to exit." in output
    assert "Sources: doc-010" in output
    assert "AI: Goodbye!" in output
    assert stub_agent.calls[0][0] == "When is the office open?"
