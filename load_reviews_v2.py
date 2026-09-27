"""
load_reviews_v2.py
--------------------
LUMINA - Reload from the real UCSD/McAuley JSON 5-core files, which
include genuine review dates (unlike the Kaggle CSV export we used
before).

This script outputs directly to processed/all_unique_reviews.csv,
using the same column names (review, rating, category) that
clean_reviews.py and sentiment_analysis.py already expect - so
those two scripts can run UNCHANGED on this new data, and the date
columns will ride along automatically since neither of those scripts
drops extra columns.

Run:
    python load_reviews_v2.py

Then continue the pipeline as before:
    python clean_reviews.py
    python sentiment_analysis.py
    (then the updated theme_validation.py, which now keeps dates)
"""

import pandas as pd
import gzip
import json
from pathlib import Path

RAW_DATA_DIR = Path("raw_data_v2")

CATEGORY_FILES = {
    "Amazon Fashion": "AMAZON_FASHION_5.json.gz",
    "Digital Music": "Digital_Music_5.json.gz",
    "Arts, Crafts and Sewing": "Arts_Crafts_and_Sewing_5.json.gz",
    "Electronics": "Electronics_5.json.gz",
}

OUTPUT_FILE = Path("processed/all_unique_reviews.csv")

CHUNK_SIZE = 100_000  # rows buffered before writing to disk


def parse_gz_json(path):
    """Yield one review dict per line from a gzipped JSON-lines file."""
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main():
    print("=" * 70)
    print("LUMINA - RELOADING FROM REAL JSON DATA (WITH DATES)")
    print("=" * 70)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists():
        print(f"Removing old {OUTPUT_FILE} ...")
        OUTPUT_FILE.unlink()

    first_write = True
    total_written = 0

    for category, filename in CATEGORY_FILES.items():
        path = RAW_DATA_DIR / filename
        if not path.exists():
            print(f"[WARNING] Skipping '{category}' — file not found: {path}")
            continue

        print(f"\nLoading category: {category} ({filename})")

        buffer = []
        count = 0

        for review in parse_gz_json(path):
            row = {
                "review": review.get("reviewText", ""),
                "rating": review.get("overall", None),
                "category": category,
                "reviewTime": review.get("reviewTime", ""),
                "unixReviewTime": review.get("unixReviewTime", None),
                "verified": review.get("verified", None),
                "reviewerID": review.get("reviewerID", ""),
            }
            buffer.append(row)
            count += 1

            if len(buffer) >= CHUNK_SIZE:
                df = pd.DataFrame(buffer)
                df.to_csv(OUTPUT_FILE, mode="w" if first_write else "a",
                          header=first_write, index=False)
                first_write = False
                total_written += len(df)
                buffer = []
                print(f"  ...{count:,} reviews loaded so far")

        # write any remaining rows
        if buffer:
            df = pd.DataFrame(buffer)
            df.to_csv(OUTPUT_FILE, mode="w" if first_write else "a",
                      header=first_write, index=False)
            first_write = False
            total_written += len(df)

        print(f"  Loaded {category}: {count:,} reviews total")

    print("\n" + "=" * 70)
    print("RELOAD COMPLETE")
    print("=" * 70)
    print(f"Total reviews written: {total_written:,}")
    print(f"Output: {OUTPUT_FILE}")
    print("\nNext steps:")
    print("  python clean_reviews.py")
    print("  python sentiment_analysis.py")
    print("  (then the updated theme_validation.py)")


if __name__ == "__main__":
    main()