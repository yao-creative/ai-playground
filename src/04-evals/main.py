import argparse
import asyncio
import sys
import time
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from answerer import OpenAIAnswerer
from dataset import load_examples
from documents import build_documents
from domain import EvalExample, RunRecord
from reporting import summarize_runs, write_run_record
from retriever import BM25Retriever
from scorers import GoldDocHitAtKScorer
from settings import load_settings


def build_answerer(settings):
    if not settings.api_key:
        raise ValueError("OPENAI_API_KEY is required to run evals.")
    return OpenAIAnswerer(api_key=settings.api_key, model=settings.model)


def run_example(example: EvalExample, documents, retriever, answerer, scorers, settings) -> RunRecord:
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
    return run_record


async def run_example_with_semaphore(
    semaphore: asyncio.Semaphore,
    example: EvalExample,
    documents,
    retriever,
    answerer,
    scorers,
    settings,
) -> RunRecord:
    async with semaphore:
        return await asyncio.to_thread(
            run_example,
            example,
            documents,
            retriever,
            answerer,
            scorers,
            settings,
        )


async def run_all_examples(examples, documents, retriever, answerer, scorers, settings) -> list[RunRecord]:
    semaphore = asyncio.Semaphore(settings.max_concurrency)
    tasks = []
    async with asyncio.TaskGroup() as task_group:
        for example in examples:
            task = task_group.create_task(
                run_example_with_semaphore(
                    semaphore,
                    example,
                    documents,
                    retriever,
                    answerer,
                    scorers,
                    settings,
                )
            )
            tasks.append(task)
    return [task.result() for task in tasks]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the 04 minimal eval harness exercise.")
    parser.add_argument("--dataset", type=Path, default=None, help="Override the JSONL dataset path.")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="Directory to write per-example JSON run records into.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Maximum number of concurrent eval examples to run.",
    )
    args = parser.parse_args()

    settings = load_settings(max_concurrency=args.max_concurrency, runs_dir=args.runs_dir)
    documents = build_documents()
    examples = load_examples(args.dataset)
    retriever = BM25Retriever(settings.model)
    answerer = build_answerer(settings)
    scorers = [GoldDocHitAtKScorer(k=settings.retrieval_limit)]
    run_records = asyncio.run(
        run_all_examples(examples, documents, retriever, answerer, scorers, settings)
    )

    print(summarize_runs(run_records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
