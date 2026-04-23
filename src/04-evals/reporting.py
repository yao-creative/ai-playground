import json
from collections import defaultdict
from pathlib import Path

from domain import RunRecord


def write_run_record(run_record: RunRecord, runs_dir: Path) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{run_record.example_id}.json"

    # Structured local run logs are the prerequisite integration point for hosted eval backends.
    with path.open("w") as output_file:
        json.dump(run_record.to_dict(), output_file, indent=2)
        output_file.write("\n")

    return path


def summarize_runs(run_records: list[RunRecord]) -> str:
    total_examples = len(run_records)
    aggregate_scores: dict[str, list[float]] = defaultdict(list)
    failures_by_category: dict[str, list[str]] = defaultdict(list)

    for run_record in run_records:
        for scorer_result in run_record.scorer_results:
            aggregate_scores[scorer_result.name].append(scorer_result.score)
            if not scorer_result.passed:
                failures_by_category[run_record.category].append(run_record.example_id)

    lines = [f"examples_run={total_examples}"]

    for scorer_name, scores in sorted(aggregate_scores.items()):
        average_score = sum(scores) / len(scores) if scores else 0.0
        lines.append(f"{scorer_name}={average_score:.2f}")

    if failures_by_category:
        lines.append("failures_by_category:")
        for category, example_ids in sorted(failures_by_category.items()):
            lines.append(f"  {category}: {', '.join(example_ids)}")

    return "\n".join(lines)
