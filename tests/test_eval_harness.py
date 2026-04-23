import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "src" / "04-evals"

if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from dataset import load_examples
from documents import build_documents
from domain import AnswerResult, EvalExample, RetrievedDoc, RunRecord, Usage
from reporting import write_run_record
from retriever import BM25Retriever
from scorers import GoldDocHitAtKScorer


def load_main_module():
    spec = importlib.util.spec_from_file_location("evals04_main", EVAL_DIR / "main.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_examples_reads_jsonl_dataset() -> None:
    examples = load_examples()

    assert len(examples) == 20
    assert examples[0].id == "ex-001"
    assert examples[0].gold_doc_ids == ["doc-001"]


def test_bm25_retriever_returns_expected_gold_doc_for_direct_query() -> None:
    retriever = BM25Retriever("gpt-5-mini")
    documents = build_documents()

    retrieved_docs = retriever.retrieve("How many remote days are allowed each week?", documents, limit=3)

    assert retrieved_docs
    assert retrieved_docs[0].id == "doc-001"


def test_write_run_record_serializes_required_fields(tmp_path: Path) -> None:
    run_record = RunRecord(
        example_id="ex-001",
        question="How many remote days are allowed each week?",
        category="direct_lookup",
        expected_answer_notes="Mention three days and manager approval.",
        gold_doc_ids=["doc-001"],
        retrieved_docs=[
            RetrievedDoc(
                id="doc-001",
                title="Remote Work Policy",
                category="hr",
                text="Employees may work remotely up to three days per week with manager approval.",
                rank=1,
                score=0.9,
            )
        ],
        final_prompt="prompt",
        answer="answer",
        latency_ms=12.5,
        model="gpt-5-mini",
        usage=Usage(),
    )

    path = write_run_record(run_record, tmp_path)
    payload = json.loads(path.read_text())

    assert payload["example_id"] == "ex-001"
    assert payload["retrieved_docs"][0]["id"] == "doc-001"
    assert payload["scorer_results"] == []


def test_gold_doc_hit_at_k_passes_and_fails() -> None:
    scorer = GoldDocHitAtKScorer(k=2)
    example = EvalExample(
        id="ex-001",
        question="How many remote days are allowed each week?",
        expected_answer_notes="Mention three days and manager approval.",
        gold_doc_ids=["doc-001"],
        category="direct_lookup",
    )
    passing_run = RunRecord(
        example_id=example.id,
        question=example.question,
        category=example.category,
        expected_answer_notes=example.expected_answer_notes,
        gold_doc_ids=example.gold_doc_ids,
        retrieved_docs=[
            RetrievedDoc(
                id="doc-001",
                title="Remote Work Policy",
                category="hr",
                text="Employees may work remotely up to three days per week with manager approval.",
                rank=1,
                score=0.9,
            )
        ],
        final_prompt="prompt",
        answer="answer",
        latency_ms=5.0,
        model="gpt-5-mini",
        usage=Usage(),
    )
    failing_run = RunRecord(
        example_id=example.id,
        question=example.question,
        category=example.category,
        expected_answer_notes=example.expected_answer_notes,
        gold_doc_ids=example.gold_doc_ids,
        retrieved_docs=[
            RetrievedDoc(
                id="doc-002",
                title="Annual Leave Guidelines",
                category="hr",
                text="Full-time employees receive 18 days of annual leave each calendar year.",
                rank=1,
                score=0.6,
            )
        ],
        final_prompt="prompt",
        answer="answer",
        latency_ms=5.0,
        model="gpt-5-mini",
        usage=Usage(),
    )

    passing_result = scorer.score(example, passing_run)
    failing_result = scorer.score(example, failing_run)

    assert passing_result.passed is True
    assert passing_result.score == 1.0
    assert failing_result.passed is False
    assert failing_result.score == 0.0


def test_build_answerer_requires_api_key() -> None:
    main = load_main_module()
    settings = SimpleNamespace(api_key=None, model="gpt-5-mini")

    try:
        main.build_answerer(settings)
    except ValueError as error:
        assert "OPENAI_API_KEY is required" in str(error)
    else:
        raise AssertionError("Expected build_answerer to reject missing API keys.")


def test_run_all_examples_respects_semaphore_and_writes_records(tmp_path: Path) -> None:
    main = load_main_module()
    examples = load_examples()[:3]
    documents = build_documents()
    retriever = BM25Retriever("gpt-5-mini")

    class FakeAnswerer:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def answer(self, question: str, retrieved_docs: list[RetrievedDoc]) -> AnswerResult:
            self.calls.append(question)
            return AnswerResult(
                answer=f"stubbed answer for {question}",
                prompt=f"prompt for {question}",
                model="fake-answerer",
                usage=Usage(),
            )

    answerer = FakeAnswerer()
    scorers = [GoldDocHitAtKScorer(k=3)]
    settings = SimpleNamespace(retrieval_limit=3, runs_dir=tmp_path, max_concurrency=2)

    run_records = main.asyncio.run(
        main.run_all_examples(examples, documents, retriever, answerer, scorers, settings)
    )

    assert [run_record.example_id for run_record in run_records] == [example.id for example in examples]
    assert len(answerer.calls) == len(examples)
    assert (tmp_path / "ex-001.json").exists()
