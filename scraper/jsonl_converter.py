"""
ResellRadar Raw-to-JSONL Handoff Converter (Person 1 -> Person 2)

Converts raw JSON-array batch files from the ingestion layer (data/raw/*.json)
into newline-delimited JSON for Person 2's PySpark pipeline
(data/processed/raw_listings.jsonl).

Design goals:
- Stream file-by-file, line-by-line (no full 50k+ in-memory load)
- Deterministic across the team: sort by stable run timestamp + run ID
- Fail loudly on malformed raw files (raw zone must stay clean)

Usage:
    python -m scraper.jsonl_converter                       # rebuild from all raw files
    python -m scraper.jsonl_converter --file data/raw/raw_all_x.json
    python -m scraper.jsonl_converter --output custom.jsonl
"""

import argparse
import json
import os
from typing import Any, Dict, IO, List, Tuple

DEFAULT_OUTPUT = "data/processed/raw_listings.jsonl"


def extract_run_id(filename: str) -> str:
    """Extract run id from 'raw_<category>_<YYYY_MM_DD_HHMMSS>_<run_id>.json'.

    run_id is optional for backward compatibility with older batch files.
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    parts = stem.split("_")
    if len(parts) >= 7:
        return parts[6]
    return "legacy"


def extract_run_timestamp(filename: str) -> str:
    """Extract the run timestamp segment from a batch filename."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    parts = stem.split("_")
    if len(parts) >= 6:
        # raw_ _ <category _ YYYY _ MM _ DD _ HHMMSS>  -> parts[2:6]
        return "_".join(parts[2:6])
    return "legacy"


def sort_key(filename: str) -> Tuple[str, str, str]:
    """Deterministic order: run timestamp first, then run id, then name."""
    return (
        extract_run_timestamp(filename),
        extract_run_id(filename),
        os.path.basename(filename),
    )


def list_raw_files(raw_dir: str = "data/raw") -> List[str]:
    """All raw JSON batch files in the ingestion zone, sorted deterministically."""
    if not os.path.isdir(raw_dir):
        return []
    files = [
        os.path.join(raw_dir, f)
        for f in os.listdir(raw_dir)
        if f.endswith(".json")
    ]
    return sorted(files, key=sort_key)


def convert_file(filepath: str, out_handle: IO[str]) -> Tuple[int, int]:
    """Stream one raw JSON array file into the JSONL output handle.

    Returns (rows_converted, rows_skipped).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed raw file {filepath}: {e}") from e

    if not isinstance(data, list):
        raise ValueError(f"Raw files must be JSON arrays of listings: {filepath}")

    rows = 0
    skipped = 0
    for record in data:
        if not isinstance(record, dict):
            skipped += 1
            continue
        out_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        rows += 1
    return rows, skipped


def convert(
    raw_dir: str = "data/raw",
    output_path: str = DEFAULT_OUTPUT,
    quiet: bool = False,
) -> Dict[str, Any]:
    """Rebuild the full JSONL handoff file from all raw JSON batches."""
    files = list_raw_files(raw_dir)
    if not files:
        return {
            "status": "NO_RAW_FILES",
            "files_converted": 0,
            "rows_converted": 0,
            "output_path": output_path,
        }

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    converted_rows = 0
    skipped_rows = 0
    used_files = []

    with open(output_path, "w", encoding="utf-8") as out:
        for filepath in files:
            rows, skipped = convert_file(filepath, out)
            converted_rows += rows
            skipped_rows += skipped
            used_files.append(os.path.basename(filepath))
            if not quiet:
                print(f"[CONVERT] {os.path.basename(filepath)} -> {rows:,} rows")

    return {
        "status": "SUCCESS",
        "files_converted": len(used_files),
        "rows_converted": converted_rows,
        "rows_skipped": skipped_rows,
        "output_path": output_path,
        "files": used_files,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert raw JSON batches to JSONL for Person 2's Spark pipeline"
    )
    parser.add_argument(
        "--file", help="Convert a single raw JSON file instead of all raw files"
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSONL path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.file:
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as out:
            rows, skipped = convert_file(args.file, out)
        print(f"[DONE] {rows:,} rows -> {args.output} ({skipped} skipped)")
    else:
        result = convert(output_path=args.output, quiet=args.quiet)
        print(json.dumps(result, indent=2))
