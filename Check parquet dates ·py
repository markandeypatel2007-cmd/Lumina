"""
check_parquet_dates.py
------------------------
Checks whether processed/reviews_all_categories.parquet (the very
first output, from load_reviews.py) still has a date column. If it
does, we can rebuild the pipeline forward from there with dates kept
intact, instead of redoing everything from raw CSVs.

Run:
    python check_parquet_dates.py
"""

import pandas as pd
from pathlib import Path

PARQUET_FILE = Path("processed/reviews_all_categories.parquet")

if not PARQUET_FILE.exists():
    print(f"NOT FOUND: {PARQUET_FILE}")
    print("This file doesn't exist (or was deleted/renamed). We'll need another approach.")
else:
    df = pd.read_parquet(PARQUET_FILE)
    print(f"Found: {PARQUET_FILE}")
    print(f"Rows: {len(df):,}")
    print("\nColumns found:")
    for col in df.columns:
        print(f"  - {col}")
    print("\nFirst row as example:")
    print(df.iloc[0])