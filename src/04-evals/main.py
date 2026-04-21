import argparse
import sys
import time
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from answerer import OpenAIAnswerer, StubAnswerer
from dataset import load_examples
from documents import build_documents
from domain import RunRecord
from reporting import summarize_runs, write_run_record
from retriever import BM25Retriever
from scorers import GoldDocHitAtKScorer
from settings import load_settings


def build_answerer(settings):
    if settings.live_model_enabled:
        if not settings.api_key:
            raise ValueError("OPENAI_API_KEY is required when live evals are enabled.")
        return OpenAIAnswerer(api_key=settings.api_key, model=settings.model)
    return StubAnswerer()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the 04 minimal eval harness exercise.")
    parser.add_argument("--dataset", type=Path, default=None, help="Override the JSONL dataset path.")
    parser.add_argument(
        "--live-model",
        action="store_true",
        help="Call the real OpenAI model instead of the stub answerer.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="Directory to write per-example JSON run records into.",
    )
    args = parser.parse_args()

    settings = load_settings(live_model_enabled=args.live_model, runs_dir=args.runs_dir)
    documents = build_documents()
    examples = load_examples(args.dataset)
    retriever = BM25Retriever(settings.model)
    answerer = build_answerer(settings)
    scorers = [GoldDocHitAtKScorer(k=settings.retrieval_limit)]
    run_records: list[RunRecord] = []

    for example in examples:
        started_at = time.perf_counter()
        retrieved_docs = retriever.retrieve(example.question, documents, limit=settings.retrieval_limit)
        answer_result = answerer.answer(example.question, retrieved_docs)
        latency_ms = (time.perf_counter() - started_at) * 1000

        run_record = RunRecord(
            example_id=example.id,
            question=example.question,
            category=example.category,
            expected_answer_notes=example.expected_answer_notes,
            gold_doc_ids=example.gold_doc_ids,
            retrieved_docs=retrieved_docs,
            final_prompt=answer_result.prompt,
            answer=answer_result.answer,
            latency_ms=latency_ms,
            model=answer_result.model,
            usage=answer_result.usage,
        )
        run_record.scorer_results = [scorer.score(example, run_record) for scorer in scorers]
        write_run_record(run_record, settings.runs_dir)
        run_records.append(run_record)

    print(summarize_runs(run_records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
