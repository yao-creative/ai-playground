from collections.abc import Iterator

from datasets import get_dataset_split_names, load_dataset

from domain import PatentRecord

DATASET_NAMESPACE = "datalyes"
DEFAULT_CONFIG = "retrieval_IN"
KNOWN_CONFIGS = (
    "retrieval_IN",
    "retrieval_MIXED",
    "retrieval_OUT",
    "title2full",
    "problem2full",
    "solution2full",
    "effect2full",
    "substance2full",
    "effect2substance",
    "class_text2ipc3",
    "class_full2timing",
    "class_nli_directions",
    "para_problem",
    "para_solution",
    "clusters_inventor",
    "clusters_ext_full_ipc",
)
DEFAULT_SPLIT = "test"
DEFAULT_LIMIT = 1000
DEFAULT_MIN_CHARS = 1


def _first_string(row: dict, keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text
    return ""


def dataset_id(config: str) -> str:
    return config if "/" in config else f"{DATASET_NAMESPACE}/{config}"


def available_configs() -> list[str]:
    return list(KNOWN_CONFIGS)


def available_splits(config: str = DEFAULT_CONFIG) -> list[str]:
    ds_id = dataset_id(config)
    try:
        return list(get_dataset_split_names(ds_id))
    except Exception as exc:  # pragma: no cover - network/gated dataset error path
        message = str(exc).lower()
        if "gated dataset" in message or "cannot be accessed" in message:
            raise PermissionError(
                f"dataset {ds_id!r} is gated. Request access on Hugging Face and set HF_TOKEN."
            ) from exc
        raise


def iter_patent_records(
    *,
    config: str = DEFAULT_CONFIG,
    split: str = DEFAULT_SPLIT,
    limit: int = DEFAULT_LIMIT,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> Iterator[PatentRecord]:
    if limit < 1:
        raise ValueError(f"limit must be >= 1, got {limit}")
    if min_chars < 0:
        raise ValueError(f"min_chars must be >= 0, got {min_chars}")

    ds_id = dataset_id(config)
    splits = available_splits(config)
    if split not in splits:
        raise ValueError(f"invalid split={split!r} for config={config!r}; expected one of {splits}")

    # v0: keep the implementation dead simple by slicing into an in-memory dataset.
    split_spec = f"{split}[:{limit}]"
    try:
        rows = load_dataset(ds_id, split=split_spec, streaming=False)
    except Exception as exc:  # pragma: no cover - network/gated dataset error path
        message = str(exc).lower()
        if "gated dataset" in message or "cannot be accessed" in message:
            raise PermissionError(
                f"dataset {ds_id!r} is gated. Request access on Hugging Face and set HF_TOKEN."
            ) from exc
        raise

    for index, row in enumerate(rows):
        short_text = _first_string(row, ["q_text", "query", "q", "problem", "title", "abstract"])
        long_text = _first_string(row, ["full_text", "text", "description", "pos", "neg", "solution"])
        text = f"{short_text}\n\n{long_text}".strip() if long_text and long_text != short_text else short_text
        if len(text) < min_chars:
            continue

        yield PatentRecord(
            id=f"{config}:{split}:{index}",
            config=config,
            split=split,
            abstract=short_text,
            description=long_text,
            text=text,
        )


def load_patent_records(
    *,
    config: str = DEFAULT_CONFIG,
    split: str = DEFAULT_SPLIT,
    limit: int = DEFAULT_LIMIT,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> list[PatentRecord]:
    return list(
        iter_patent_records(
            config=config,
            split=split,
            limit=limit,
            min_chars=min_chars,
        )
    )
