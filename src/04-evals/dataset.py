import json
from pathlib import Path

from domain import EvalExample


def default_dataset_path() -> Path:
    return Path(__file__).with_name("examples.jsonl")


def load_examples(dataset_path: Path | None = None) -> list[EvalExample]:
    path = dataset_path or default_dataset_path()
    examples: list[EvalExample] = []

    with path.open() as dataset_file:
        for line_number, raw_line in enumerate(dataset_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            payload = json.loads(line)
            try:
                examples.append(
                    EvalExample(
                        id=payload["id"],
                        question=payload["question"],
                        expected_answer_notes=payload["expected_answer_notes"],
                        gold_doc_ids=list(payload["gold_doc_ids"]),
                        category=payload["category"],
                    )
                )
            except KeyError as exc:
                raise ValueError(f"dataset row {line_number} is missing required field {exc}") from exc

    return examples
