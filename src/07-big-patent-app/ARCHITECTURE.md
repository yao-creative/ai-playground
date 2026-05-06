# 06-big-patent-app Architecture

## Scope

This app is now hard-cut to PatenTEB (`datalyes/*`) while keeping the previous command form and app path.

## Current v0 architecture

- Loader entrypoint: `iter_patent_records(config, split, limit, min_chars)`
- Upstream source mapping:
  - `config=retrieval_IN` -> `datalyes/retrieval_IN`
  - generally `config=<task>` -> `datalyes/<task>`
- Output schema: `PatentRecord(id, config, split, abstract, description, text)`
- CLI modes:
  - `preview`
  - `stats`
  - `jsonl` (+ metadata sidecar)

## Sequence diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as main.py
    participant Loader as loader.py
    participant HF as HuggingFace datasets
    participant FS as JSONL output

    User->>CLI: run --config --split --limit --mode
    CLI->>Loader: iter_patent_records(config, split, limit, min_chars)
    Loader->>HF: load_dataset(\"datalyes/<config>\", split=\"<split>[:limit]\")
    HF-->>Loader: rows
    Loader-->>CLI: PatentRecord stream

    alt mode=preview
        CLI-->>User: print first N rows
    else mode=stats
        CLI-->>User: print rows + avg_text_chars
    else mode=jsonl
        CLI->>FS: write rows.jsonl
        CLI->>FS: write rows.jsonl.meta.json
        CLI-->>User: output paths
    end
```

## Operational notes

- Many PatenTEB datasets are gated; access approval and `HF_TOKEN` are required.
- The app intentionally keeps the old interface to avoid workflow breaks.
- Generated artifacts are ignored via `.gitignore` rule `data/*`.
