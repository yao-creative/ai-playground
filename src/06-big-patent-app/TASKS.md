# BIGPATENT Search Tasks (Doable Roadmap)

This file lists practical tasks to demo search over BIGPATENT first, then expand into related patent NLP tasks.

## What is validated online

- BIGPATENT on Hugging Face is a summarization dataset with `description` and `abstract` fields, split into `train/validation/test`, with CPC category configs (`a,b,c,d,e,f,g,h,y,all`):  
  https://huggingface.co/datasets/NortheasternUniversity/big_patent/blob/main/README.md
- BIGPATENT paper/problem framing (abstractive summarization over patent docs):  
  https://huggingface.co/papers/1906.03741
- Related prior-art matching task benchmark (PatentMatch):  
  https://huggingface.co/papers/2012.13919
- Larger related patent corpus with multiple tasks (HUPD):  
  https://huggingface.co/datasets/HUPD/hupd/tree/main
- Large-scale patent analytics source (Google Patents public datasets):  
  https://github.com/google/patents-public-data

## Phase 1: MVP tasks for BIGPATENT search (recommended for demo)

1. Build a fixed demo corpus export (0.5 day)
- Export `config=all`, `split=train`, `limit=5000-20000` to JSONL.
- Keep deterministic IDs (`config:split:index`) and save under `data/`.
- Deliverable: one stable corpus file for repeatable demos.

2. Add lexical search baseline (0.5 day)
- Index `text = abstract + description` with BM25.
- CLI query: return top-k records with scores.
- Deliverable: `search --mode bm25 --query "..."`

3. Add vector search baseline (1 day)
- Chunk text (e.g., 512 tokens, 64 overlap), embed chunks, store vectors.
- Query embedding -> top-k vector retrieval.
- Deliverable: `search --mode vector --query "..."`

4. Add hybrid retrieval (0.5 day)
- Combine BM25 + vector scores (weighted sum or rank fusion).
- Show retrieved IDs and snippets for explainability.
- Deliverable: `search --mode hybrid --query "..."`

5. Add tiny eval set for retrieval quality (0.5 day)
- Create 30-50 hand-checked queries with expected relevant docs/chunks.
- Report `Recall@k` and `MRR`.
- Deliverable: `eval_retrieval.py` with metrics output.

6. Add answer generation on top of retrieval (0.5 day)
- Use top-k chunks as context to generate answers.
- Always show source citations and latency.
- Deliverable: demo-ready Q&A loop.

## Phase 2: Related doable tasks after MVP

1. Prior-art matching track with PatentMatch (1-2 days)
- Train/evaluate a claim-to-passage matcher.
- Reuse your retrieval pipeline as candidate generator.

2. Patent classification track with HUPD (1-2 days)
- Build CPC/topic classification baseline.
- Useful for category routing and filtered retrieval.

3. Patent analytics enrichment track (2-3 days)
- Join your retrieval outputs with Google Patents metadata for dashboards.
- Add trend slices by assignee, year, or CPC domain.

## Suggested execution order

1. Phase 1 tasks 1-3
2. Phase 1 tasks 4-6
3. Phase 2 task 1 or 2 (pick one based on demo story)

## Demo acceptance criteria

1. Query returns ranked evidence in <2s on local sample.
2. Answer includes citations to chunk/document IDs.
3. Same scripted demo questions produce stable outputs.
4. Retrieval metrics are reported for a fixed evaluation set.
