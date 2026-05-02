from datasets import get_dataset_config_names, get_dataset_split_names, load_dataset

from domain import PatentRecord

DATASET_NAME = "NortheasternUniversity/big_patent"


def available_configs() -> list[str]:
    return list(get_dataset_config_names(DATASET_NAME))


def available_splits(config: str) -> list[str]:
    return list(get_dataset_split_names(DATASET_NAME, config))


def load_patent_records(
    *,
    config: str = "all",
    split: str = "train",
    limit: int = 1000,
    min_chars: int = 1,
) -> list[PatentRecord]:
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

    records: list[PatentRecord] = []
    for index, row in enumerate(dataset):
        abstract = (row.get("abstract") or "").strip()
        description = (row.get("description") or "").strip()
        text = f"{abstract}\n\n{description}".strip()
        if len(text) < min_chars:
            continue

        records.append(
            PatentRecord(
                id=f"{config}:{split}:{index}",
                config=config,
                split=split,
                abstract=abstract,
                description=description,
                text=text,
            )
        )

    return records
