"""
check_raw_dates.py
--------------------
Checks the original raw CSV files (before any cleaning/processing)
for a date or time column, and shows a sample row from each so we
can confirm the exact column name and format.

Run:
    python check_raw_dates.py
"""

import pandas as pd
from pathlib import Path

RAW_FILES = [
    "raw_data/fashion.csv",
    "raw_data/digital_music.csv",
    "raw_data/arts_crafts_sewing.csv",
    "raw_data/electronics_1.csv",
]

for filepath in RAW_FILES:
    path = Path(filepath)
    print("=" * 70)
    print(filepath)
    print("=" * 70)

    if not path.exists():
        print("NOT FOUND - skipping")
        continue

    df = pd.read_csv(path, nrows=3)
    print("Columns:")
    for col in df.columns:
        print(f"  - {col}")

    print("\nFirst row:")
    print(df.iloc[0])
    print()