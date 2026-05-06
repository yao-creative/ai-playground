# PatenTEB Search Tasks (Doable Roadmap)

This file lists practical tasks to demo search over PatenTEB first, then expand to richer benchmark tasks.

## Source references

- PatenTEB task dataset example (`retrieval_IN`):  
  https://huggingface.co/datasets/datalyes/retrieval_IN/blob/main/README.md
- PatenTEB paper:  
  https://arxiv.org/abs/2510.22264

## Phase 1: MVP tasks (recommended)

1. Fixed corpus export (0.5 day)
- Export `config=retrieval_IN`, `split=test`, `limit=1000` to JSONL.
- Keep deterministic IDs (`config:split:index`).

2. Retrieval baseline (1 day)
- Build BM25 index on normalized `text`.
- CLI query returns top-k records with scores and IDs.

3. Vector baseline (1 day)
- Chunk and embed records.
- Query embedding -> top-k vector retrieval.

4. Hybrid retrieval (0.5 day)
- Fuse BM25 + vector rankings.
- Show source IDs/snippets in answer output.

5. Tiny retrieval eval set (0.5 day)
- 30-50 fixed demo queries with expected positives.
- Track `Recall@k` and `MRR`.

## Phase 2: task expansion (PatenTEB-native)

1. Asymmetric retrieval tasks
- `title2full`, `problem2full`, `solution2full`, `effect2full`, `substance2full`.

2. Classification tasks
- `class_text2ipc3`, `class_full2timing`, `class_nli_directions`.

3. Paraphrase/clustering tasks
- `para_problem`, `para_solution`, `clusters_inventor`, `clusters_ext_full_ipc`.

## Demo acceptance criteria

1. Query returns ranked evidence in <2s on local sample.
2. Answer includes cited source IDs.
3. Scripted demo questions produce stable outputs.
4. Export metadata (`*.meta.json`) matches row count and config/split used.
