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
