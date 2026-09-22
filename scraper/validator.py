"""
ResellRadar Raw Data Validator (Person 1 - Data Quality at the Source)

Validates raw listing files in data/raw/ against the schema contract in
scraper/SCHEMA.md, and reports aggregate data-quality metrics.

Checks:
- Required fields present and correctly typed
- ISO-8601 timestamp formats (posted_date, delisted_date, scraped_at)
- price >= 0 and price > 0 (price-zero listings are quality issues)
- listing_id uniqueness within and across files
- delisted_date must be >= posted_date when present
- category/sub_category/source_platform/seller_type allowed values

Usage:
    python -m scraper.validator                    # validate all files in data/raw
    python -m scraper.validator --file data/raw/raw_all_x.json
    python -m scraper.validator --max-error-rate 0.01

Exit code 0 = pass, 1 = validation failures found.
"""

import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

# -------------------------------------------------
# Schema contract (mirrors scraper/SCHEMA.md v1.0.0)
# -------------------------------------------------

REQUIRED_NON_NULLABLE = [
    "listing_id", "title", "description", "price", "currency",
    "category", "sub_category", "location_city", "location_region",
    "posted_date", "seller_type", "source_platform", "scraped_at",
]

NULLABLE = ["delisted_date"]

ALLOWED_CATEGORIES = {"Phones & Mobile", "Furniture & Decor"}
ALLOWED_SELLER_TYPES = {"Individual", "Verified PowerSeller", "Liquidation Depot", "Refurbisher"}
ALLOWED_SOURCES = {"Craigslist", "Facebook Marketplace", "OfferUp", "eBay Refurbished"}

ISO_8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _parse_iso(ts: str):
    """Parse an ISO-8601 UTC timestamp; returns datetime or None if invalid."""
    if not isinstance(ts, str) or not ISO_8601_RE.match(ts):
        return None
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def validate_listing(record: Dict[str, Any]) -> List[str]:
    """Return a list of error strings for a single listing (empty = valid)."""
    errors = []

    if not isinstance(record, dict):
        return ["record is not a JSON object"]

    # Required fields present + non-null
    for field in REQUIRED_NON_NULLABLE:
        value = record.get(field)
        if value is None:
            errors.append(f"missing required field '{field}'")

    if errors:
        return errors  # further checks need the fields to exist

    # Field types
    if not isinstance(record["price"], (int, float)) or isinstance(record["price"], bool):
        errors.append(f"price must be a number, got {type(record['price']).__name__}")
    for field in ("listing_id", "title", "description", "currency", "category",
                  "sub_category", "location_city", "location_region",
                  "seller_type", "source_platform"):
        if not isinstance(record[field], str):
            errors.append(f"{field} must be a string, got {type(record[field]).__name__}")

    if errors:
        return errors

    # Price quality: non-negative, and zero prices are quality issues
    if record["price"] < 0:
        errors.append(f"negative price: {record['price']}")
    elif record["price"] == 0:
        errors.append("price is 0.0 (parse failure or missing source price)")

    # Controlled vocabularies
    if record["category"] not in ALLOWED_CATEGORIES:
        errors.append(f"unknown category '{record['category']}'")
    if record["seller_type"] not in ALLOWED_SELLER_TYPES:
        errors.append(f"unknown seller_type '{record['seller_type']}'")
    if record["source_platform"] not in ALLOWED_SOURCES:
        errors.append(f"unknown source_platform '{record['source_platform']}'")

    # Timestamp formats
    posted_dt = None
    delisted_dt = None
    for field in ("posted_date", "scraped_at", "delisted_date"):
        value = record.get(field)
        if field in NULLABLE and value is None:
            continue
        parsed = _parse_iso(value)
        if parsed is None:
            errors.append(f"{field} is not ISO-8601 UTC ('YYYY-MM-DDTHH:MM:SSZ'): {value!r}")
            continue
        if field == "posted_date":
            posted_dt = parsed
        elif field == "delisted_date":
            delisted_dt = parsed

    # Temporal sanity: delisted must come after posted
    if posted_dt is not None and delisted_dt is not None and delisted_dt < posted_dt:
        errors.append("delisted_date is earlier than posted_date")

    return errors


def validate_file(filepath: str, seen_ids: Dict[str, str]) -> Dict[str, Any]:
    """Validate one raw JSON file. seen_ids maps listing_id -> first file seen.

    Mutates seen_ids to track cross-file duplicates.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "file": filepath, "records": 0, "valid": 0, "invalid": 1,
                "error_rate": 1.0,
                "errors": [f"file is not valid JSON: {e}"],
            }

    if not isinstance(data, list):
        return {
            "file": filepath, "records": 0, "valid": 0, "invalid": 1,
            "error_rate": 1.0,
            "errors": ["raw file must be a JSON array of listings"],
        }

    valid = 0
    invalid = 0
    error_counts: Dict[str, int] = {}
    examples: Dict[str, str] = {}

    for idx, record in enumerate(data):
        listing_errors = validate_listing(record)
        if listing_errors:
            invalid += 1
            for err in listing_errors:
                error_counts[err] = error_counts.get(err, 0) + 1
                if err not in examples:
                    lid = record.get("listing_id", f"<record #{idx}>") if isinstance(record, dict) else f"<record #{idx}>"
                    examples[err] = str(lid)
        else:
            valid += 1
            # Uniqueness check across the whole raw zone
            lid = record["listing_id"]
            if lid in seen_ids:
                dup_err = f"duplicate listing_id across files: {lid}"
                error_counts[dup_err] = error_counts.get(dup_err, 0) + 1
                invalid += 1
                valid -= 1
            else:
                seen_ids[lid] = filepath

    total = valid + invalid
    return {
        "file": filepath,
        "records": total,
        "valid": valid,
        "invalid": invalid,
        "error_rate": round(invalid / total, 6) if total else 0.0,
        "error_counts": error_counts,
        "examples": examples,
    }


def validate_all(raw_dir: str = "data/raw", max_error_rate: float = 0.0) -> Dict[str, Any]:
    """Validate every raw JSON file in the ingestion zone."""
    if not os.path.isdir(raw_dir):
        return {"status": "NO_RAW_FILES", "files": [], "totals": {"records": 0, "valid": 0, "invalid": 0}}

    seen_ids: Dict[str, str] = {}
    file_reports = []
    totals = {"records": 0, "valid": 0, "invalid": 0}

    for fname in sorted(os.listdir(raw_dir)):
        if not fname.endswith(".json"):
            continue
        report = validate_file(os.path.join(raw_dir, fname), seen_ids)
        file_reports.append(report)
        totals["records"] += report["records"]
        totals["valid"] += report["valid"]
        totals["invalid"] += report["invalid"]

    overall_rate = round(totals["invalid"] / totals["records"], 6) if totals["records"] else 0.0
    status = "PASS" if overall_rate <= max_error_rate else "FAIL"

    return {
        "status": status,
        "max_error_rate": max_error_rate,
        "overall_error_rate": overall_rate,
        "unique_listing_ids": len(seen_ids),
        "totals": totals,
        "files": file_reports,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate raw listings against scraper/SCHEMA.md (Person 1 quality gate)"
    )
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--file", help="Validate a single raw JSON file")
    parser.add_argument(
        "--max-error-rate", type=float, default=0.0,
        help="Maximum tolerated invalid-record ratio (default 0 = strict)"
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures")
    args = parser.parse_args()

    if args.file:
        seen: Dict[str, str] = {}
        report = validate_file(args.file, seen)
        result = {
            "status": "PASS" if report["invalid"] == 0 else "FAIL",
            "totals": {"records": report["records"], "valid": report["valid"], "invalid": report["invalid"]},
            "files": [report],
        }
    else:
        result = validate_all(args.raw_dir, args.max_error_rate)

    if not args.quiet or result["status"] == "FAIL":
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["status"] in ("PASS", "NO_RAW_FILES") else 1)
