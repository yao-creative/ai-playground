from domain import EvalExample, RunRecord, ScoreResult


class GoldDocHitAtKScorer:
    def __init__(self, k: int = 3) -> None:
        self.k = k

    def score(self, example: EvalExample, run_record: RunRecord) -> ScoreResult:
        retrieved_doc_ids = [document.id for document in run_record.retrieved_docs[: self.k]]
        matching_gold_doc_ids = [
            gold_doc_id for gold_doc_id in example.gold_doc_ids if gold_doc_id in retrieved_doc_ids
        ]
        passed = bool(matching_gold_doc_ids)

        return ScoreResult(
            name=f"gold_doc_hit_at_{self.k}",
            passed=passed,
            score=1.0 if passed else 0.0,
            comment=(
                f"expected one of {example.gold_doc_ids}; "
                f"retrieved {retrieved_doc_ids}; matched {matching_gold_doc_ids}"
            ),
        )


# Retrieval evals belong here because they score document selection before answer quality.
def all_gold_docs_recalled_placeholder() -> None:
    # Fill this in next:
    # - deterministic retrieval scorer
    # - input: EvalExample.gold_doc_ids + RunRecord.retrieved_docs
    # - design pattern: component eval, independent of the final answer text
    raise NotImplementedError


def unsupported_question_refusal_placeholder() -> None:
    # Fill this in next:
    # - deterministic answer eval
    # - input: EvalExample.category + RunRecord.answer
    # - design pattern: contract eval for "say I don't know" behavior
    raise NotImplementedError


def answer_mentions_key_fact_placeholder() -> None:
    # Fill this in next:
    # - deterministic or regex-based answer eval
    # - input: EvalExample.expected_answer_notes + RunRecord.answer
    # - design pattern: cheap local heuristic before adding judge models
    raise NotImplementedError


def llm_judge_groundedness_placeholder() -> None:
    # Fill this in next:
    # - judge-based eval
    # - input: retrieved docs + final answer
    # - design pattern: answer-level eval that checks support in context
    raise NotImplementedError


def llm_judge_correctness_placeholder() -> None:
    # Fill this in next:
    # - judge-based eval
    # - input: question + expected notes + final answer
    # - design pattern: end-to-end quality eval after deterministic checks
    raise NotImplementedError
