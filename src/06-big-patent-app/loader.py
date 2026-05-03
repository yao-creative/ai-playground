from collections.abc import Iterator

from datasets import get_dataset_config_names, get_dataset_split_names, load_dataset

from domain import PatentRecord

DATASET_NAME = "NortheasternUniversity/big_patent"
DEFAULT_CONFIG = "all"
DEFAULT_SPLIT = "train"
DEFAULT_LIMIT = 10000
DEFAULT_MIN_CHARS = 1


def available_configs() -> list[str]:
    return list(get_dataset_config_names(DATASET_NAME))


def available_splits(config: str) -> list[str]:
    return list(get_dataset_split_names(DATASET_NAME, config))


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

    configs = available_configs()
    if config not in configs:
        raise ValueError(f"invalid config={config!r}; expected one of {configs}")

    splits = available_splits(config)
    if split not in splits:
        raise ValueError(f"invalid split={split!r} for config={config!r}; expected one of {splits}")

    # v0: keep the implementation dead simple by slicing into an in-memory dataset.
    split_spec = f"{split}[:{limit}]"
    dataset = load_dataset(DATASET_NAME, name=config, split=split_spec, streaming=False)

    for index, row in enumerate(dataset):
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
