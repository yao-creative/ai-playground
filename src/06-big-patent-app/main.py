import argparse
import json
from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent.parent
MODULE_DIR = Path(__file__).resolve().parent

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(APP_DIR) not in sys.path:
    sys.path.insert(1, str(APP_DIR))

from loader import load_patent_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BIGPATENT v0 in-memory dataloader")
    parser.add_argument("--config", default="all", help="Dataset config (default: all)")
    parser.add_argument("--split", default="train", help="Split name (default: train)")
    parser.add_argument("--limit", type=int, default=1000, help="Number of rows to load (default: 1000)")
    parser.add_argument("--min-chars", type=int, default=1, help="Minimum chars in normalized text")
    parser.add_argument(
        "--mode",
        choices=["preview", "jsonl", "stats"],
        default="preview",
        help="Output mode: preview, jsonl, or stats",
    )
    parser.add_argument("--out", type=Path, help="Output JSONL path when --mode jsonl")
    parser.add_argument("--preview-count", type=int, default=3, help="Rows shown in preview mode")
    return parser.parse_args()


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def main() -> None:
    args = parse_args()
    records = load_patent_records(
        config=args.config,
        split=args.split,
        limit=args.limit,
        min_chars=args.min_chars,
    )

    if args.mode == "stats":
        text_lengths = [len(record.text) for record in records]
        avg_len = (sum(text_lengths) / len(text_lengths)) if text_lengths else 0.0
        print(f"rows={len(records)}")
        print(f"avg_text_chars={avg_len:.2f}")
        return

    if args.mode == "jsonl":
        if args.out is None:
            raise ValueError("--out is required when --mode jsonl")
        write_jsonl(args.out, [record.to_dict() for record in records])
        print(f"wrote {len(records)} rows to {args.out}")
        return

    preview_count = max(1, args.preview_count)
    for record in records[:preview_count]:
        print(json.dumps(record.to_dict(), ensure_ascii=True))


if __name__ == "__main__":
    main()
