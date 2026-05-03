import argparse
from collections.abc import Iterator
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent.parent
MODULE_DIR = Path(__file__).resolve().parent

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(APP_DIR) not in sys.path:
    sys.path.insert(1, str(APP_DIR))

from domain import PatentRecord
from loader import (
    DEFAULT_CONFIG,
    DEFAULT_LIMIT,
    DEFAULT_MIN_CHARS,
    DEFAULT_SPLIT,
    iter_patent_records,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BIGPATENT v0 in-memory dataloader")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Dataset config (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--split",
        default=DEFAULT_SPLIT,
        help=f"Split name (default: {DEFAULT_SPLIT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Number of rows to load (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=DEFAULT_MIN_CHARS,
        help=f"Minimum chars in normalized text (default: {DEFAULT_MIN_CHARS})",
    )
    parser.add_argument(
        "--mode",
        choices=["preview", "jsonl", "stats"],
        default="preview",
        help="Output mode: preview, jsonl, or stats",
    )
    parser.add_argument("--out", type=Path, help="Output JSONL path when --mode jsonl")
    parser.add_argument("--preview-count", type=int, default=3, help="Rows shown in preview mode")
    return parser.parse_args()


def export_jsonl(path: Path, records: Iterator[PatentRecord]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=True) + "\n")
            rows_written += 1
    return rows_written


def write_export_metadata(path: Path, *, config: str, split: str, limit: int, min_chars: int, row_count: int) -> Path:
    metadata_path = path.with_suffix(f"{path.suffix}.meta.json")
    payload = {
        "dataset": "NortheasternUniversity/big_patent",
        "config": config,
        "split": split,
        "limit": limit,
        "min_chars": min_chars,
        "row_count": row_count,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    return metadata_path


def main() -> None:
    args = parse_args()
    if args.mode == "stats":
        total_rows = 0
        total_chars = 0
        for record in iter_patent_records(
            config=args.config,
            split=args.split,
            limit=args.limit,
            min_chars=args.min_chars,
        ):
            total_rows += 1
            total_chars += len(record.text)
        avg_len = (total_chars / total_rows) if total_rows else 0.0
        print(f"rows={total_rows}")
        print(f"avg_text_chars={avg_len:.2f}")
        return

    if args.mode == "jsonl":
        if args.out is None:
            raise ValueError("--out is required when --mode jsonl")
        rows_written = export_jsonl(
            args.out,
            iter_patent_records(
                config=args.config,
                split=args.split,
                limit=args.limit,
                min_chars=args.min_chars,
            ),
        )
        metadata_path = write_export_metadata(
            args.out,
            config=args.config,
            split=args.split,
            limit=args.limit,
            min_chars=args.min_chars,
            row_count=rows_written,
        )
        print(f"wrote {rows_written} rows to {args.out}")
        print(f"wrote metadata to {metadata_path}")
        return

    preview_count = max(1, args.preview_count)
    for index, record in enumerate(
        iter_patent_records(
            config=args.config,
            split=args.split,
            limit=args.limit,
            min_chars=args.min_chars,
        )
    ):
        if index >= preview_count:
            break
        print(json.dumps(record.to_dict(), ensure_ascii=True))


if __name__ == "__main__":
    main()
