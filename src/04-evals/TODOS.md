# 04 Evals Tutorial Todos

This folder is meant to teach evals in layers. Do these in order and keep each step small.

## 1. Read The Current Shape

- [ ] Read `README.md` and trace the execution flow in `main.py`.
- [ ] Inspect `domain.py` and identify the core interfaces: `Retriever`, `Answerer`, `Scorer`.
- [ ] Run the script once and inspect one JSON file in `.eval-runs/04-evals/`.
- [ ] Explain to yourself what is being evaluated today vs what is only scaffolded.

## 2. Understand The Dataset

- [ ] Open `examples.jsonl` and group the rows by category.
- [ ] Add 5 more hand-written examples:
- [ ] Include at least 2 unsupported questions.
- [ ] Include at least 2 paraphrase questions.
- [ ] Include at least 1 multi-fact question.
- [ ] Add one intentionally tricky example that should be hard for BM25.
- [ ] Document why each category exists and what failure mode it represents.

## 3. Learn Retrieval Evals First

- [ ] Read `retriever.py` and understand how document text is serialized and indexed.
- [ ] Print the top 3 retrieved docs for 3 example questions.
- [ ] Implement `all_gold_docs_recalled_placeholder` in `scorers.py`.
- [ ] Add a retrieval summary metric:
- [ ] `hit@k`
- [ ] `recall@k`
- [ ] average top-rank position for a gold doc
- [ ] Add a report section that shows the worst retrieval misses.
- [ ] For one failed example, write down whether the problem is tokenization, ranking, or dataset ambiguity.

## 4. Improve The Dataset For Better Evals

- [ ] Add `difficulty` or `notes` to the JSONL schema if you need richer annotations.
- [ ] Add one example with multiple valid gold docs.
- [ ] Add one example where no document should be retrieved confidently.
- [ ] Decide whether unsupported cases should have `gold_doc_ids=[]` or one reference doc plus a refusal note.
- [ ] Update loader code if you change the schema.

## 5. Learn Prompt And Answer Architecture

- [ ] Read `answerer.py` and inspect the prompt built by `build_prompt`.
- [ ] Compare two prompt variants on the same retrieval results.
- [ ] Rewrite the system prompt once to be stricter about unsupported answers.
- [ ] Add a second prompt variant for comparison.
- [ ] Add a CLI flag or constant to switch prompt variants.
- [ ] Save the prompt variant name into `RunRecord`.

## 6. Add Cheap Deterministic Answer Evals

- [ ] Implement `unsupported_question_refusal_placeholder`.
- [ ] Decide what counts as a refusal:
- [ ] explicit uncertainty
- [ ] no fabricated policy detail
- [ ] no false confidence
- [ ] Implement `answer_mentions_key_fact_placeholder`.
- [ ] Start with one simple heuristic:
- [ ] keyword presence
- [ ] phrase match
- [ ] number/date presence
- [ ] Record false positives and false negatives for the heuristic.

## 7. Add Judge-Based Evals Carefully

- [ ] Implement `llm_judge_groundedness_placeholder`.
- [ ] Use retrieved docs plus answer as the judge input.
- [ ] Define a small scoring rubric before writing the judge prompt.
- [ ] Implement `llm_judge_correctness_placeholder`.
- [ ] Use question, expected notes, and answer as the judge input.
- [ ] Save judge reasoning and raw score into the run record.
- [ ] Compare judge results against at least 5 manually inspected examples.

## 8. Separate Eval Facets Explicitly

- [ ] Make a table for every scorer:
- [ ] what layer it evaluates
- [ ] whether it is deterministic or judge-based
- [ ] whether it is cheap enough for every run
- [ ] whether it should gate CI
- [ ] Split scorers into:
- [ ] retrieval evals
- [ ] answer contract evals
- [ ] answer quality evals
- [ ] future online evals

## 9. Improve Reporting

- [ ] Extend `reporting.py` to show per-category averages.
- [ ] Print the top failing example ids per scorer.
- [ ] Print one retrieval miss example with question, gold docs, and retrieved docs.
- [ ] Print one answer-quality failure example once you add answer evals.
- [ ] Add a markdown report writer in addition to JSON run records.

## 10. Add Better Modular Integration Seams

- [ ] Add a real provider adapter layer if you want more than OpenAI.
- [ ] Add an embedding retriever beside BM25.
- [ ] Add a reranker after retrieval.
- [ ] Add a prompt-template module if prompt variations multiply.
- [ ] Add backend exporters only after local run records are stable.
- [ ] Leave `main.py` thin and keep orchestration logic out of scorers.

## 11. Compare Variants

- [ ] Compare BM25 vs future embedding retrieval on the same dataset.
- [ ] Compare prompt A vs prompt B on unsupported questions.
- [ ] Compare prompt A vs prompt B on the same retrieval results.
- [ ] Write down what changed in retrieval quality vs final answer quality.
- [ ] Avoid changing retrieval and prompt at the same time unless you are doing a deliberate experiment.

## 12. Turn This Into A Real Eval Harness

- [ ] Add a frozen regression dataset.
- [ ] Add a baseline report you can compare against.
- [ ] Add thresholds for passing:
- [ ] minimum retrieval hit rate
- [ ] minimum refusal compliance
- [ ] minimum groundedness score
- [ ] Add a CI-friendly mode that runs only deterministic evals.
- [ ] Add a slower mode that includes judge-based scoring.
- [ ] Decide when a failure should block a change vs only be logged.

## 13. Reflection Questions

- [ ] Which failures came from retrieval vs generation?
- [ ] Which evals were cheap and reliable?
- [ ] Which evals were noisy?
- [ ] Which annotations in the dataset were missing?
- [ ] What would need to change before this could support tools, memory, or agents?
