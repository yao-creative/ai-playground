# 06-big-patent-app (v0)

Minimal BIGPATENT loader for local experimentation.

## What it does

- loads a small in-memory slice from `NortheasternUniversity/big_patent`
- normalizes each row into:
  - `id`
  - `config`
  - `split`
  - `abstract`
  - `description`
  - `text` (`abstract + "\n\n" + description`)
- supports `preview`, `stats`, and `jsonl` output modes

## Sequence diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as main.py
    participant Loader as loader.py
    participant HF as HuggingFace datasets
    participant Domain as domain.py
    participant FS as Filesystem (optional)

    User->>CLI: run with args (--config --split --limit --mode ...)
    CLI->>Loader: load_patent_records(config, split, limit, min_chars)

    Loader->>HF: get_dataset_config_names(DATASET_NAME)
    HF-->>Loader: configs
    Loader->>HF: get_dataset_split_names(DATASET_NAME, config)
    HF-->>Loader: splits
    Loader->>HF: load_dataset(name=config, split=f"{split}[:{limit}]", streaming=False)
    HF-->>Loader: in-memory rows

    loop each row
        Loader->>Loader: normalize abstract/description/text
        Loader->>Domain: PatentRecord(...)
        Domain-->>Loader: record
    end

    Loader-->>CLI: list[PatentRecord]

    alt mode=preview
        CLI->>CLI: print first N records as JSON
    else mode=stats
        CLI->>CLI: compute rows + avg_text_chars
        CLI-->>User: print stats
    else mode=jsonl
        CLI->>FS: write JSONL via write_jsonl(...)
        FS-->>CLI: done
        CLI-->>User: wrote N rows
    end
```

## Example usage

Preview first 2 rows from a small slice:

```bash
uv run python src/06-big-patent-app/main.py \
  --config all \
  --split train \
  --limit 20 \
  --mode preview \
  --preview-count 2
```

Show quick stats:

```bash
uv run python src/06-big-patent-app/main.py \
  --config all \
  --split train \
  --limit 100 \
  --mode stats
```

Write JSONL:

```bash
uv run python src/06-big-patent-app/main.py \
  --config all \
  --split train \
  --limit 100 \
  --mode jsonl \
  --out data/big_patent_v0_sample.jsonl
```

## Notes

- This is intentionally non-streaming to keep iteration simple.
- For larger ingestion pipelines, the next step is a streaming iterator with batching and checkpoints.

## Next steps: data loading patterns

1. Keep one stable ingestion interface:
   - `iter_patent_records(config, split, limit=None, min_chars=1)`
   - v0 implementation can wrap `load_patent_records`; future versions swap backend only.
2. Add v1 streaming backend:
   - use `load_dataset(..., streaming=True)` for full-corpus processing.
   - preserve the same `PatentRecord` schema so downstream code does not change.
3. Add batched iteration:
   - `iter_patent_batches(..., batch_size=32)` for embedding/index pipelines.
4. Add checkpoint/resume:
   - persist `{config, split, last_index}` every N rows to continue interrupted jobs.
5. Add partition-aware export:
   - write JSONL shards like `data/big_patent/all/train/part-0001.jsonl` for parallel indexing.
6. Add quality filters:
   - enforce `min_chars`, max length truncation, and optional dedupe hash on `text`.
7. Add deterministic sampling:
   - `sample_seed` + `sample_rate` for repeatable small experiments without full loads.
8. Add observability:
   - periodic progress logs (`processed`, `kept`, `filtered`) and elapsed time per 10k rows.

## Why "v0 can wrap load_patent_records"

The idea is to keep downstream code calling one iterator interface while the backend changes.

In v0, `iter_patent_records` just calls `load_patent_records` and yields the list:

```python
def iter_patent_records(config="all", split="train", limit=1000, min_chars=1):
    rows = load_patent_records(
        config=config,
        split=split,
        limit=limit,
        min_chars=min_chars,
    )
    for row in rows:
        yield row
```

Later, the same function name can switch to streaming without changing callers.

## What streaming solves

- avoids loading large splits fully into memory
- allows full-corpus processing (millions of rows) in one pass
- improves robustness for long jobs when combined with checkpoints
- reduces startup latency for pipeline-style ingestion jobs

Streaming mainly solves scale and reliability issues, not model quality by itself.

## Streaming integration point and usage

The integration point is the loader interface (`iter_patent_records`), not the CLI output code.

Keep `main.py` consuming an iterator, then swap the loader implementation:

```python
from datasets import load_dataset

def iter_patent_records(config="all", split="train", min_chars=1):
    ds = load_dataset(
        "NortheasternUniversity/big_patent",
        name=config,
        split=split,
        streaming=True,
    )
    for index, row in enumerate(ds):
        abstract = (row.get("abstract") or "").strip()
        description = (row.get("description") or "").strip()
        text = f"{abstract}\n\n{description}".strip()
        if len(text) < min_chars:
            continue
        yield PatentRecord(
            id=f"{config}:{split}:{index}",
            config=config,
            split=split,
            abstract=abstract,
            description=description,
            text=text,
        )
```

Any consumer (preview/stats/jsonl/embed/index) can keep using the same iterator contract.

## Where data is saved

There are two different storage locations:

1. Your app output file (JSONL export):
   - controlled by `--out`
   - current example: `data/big_patent_v0_sample.jsonl`
   - in the Make target, default is also `data/big_patent_v0_sample.jsonl`
2. Hugging Face dataset cache files:
   - managed by the `datasets` library
   - default location is your local HF cache directory (for example under `~/.cache/huggingface`)
   - can be redirected with HF cache environment variables when needed
