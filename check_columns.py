"""
check_columns.py
-----------------
Quick diagnostic - prints the column names and a sample row from
processed/reviews_sentiment.csv, so we can confirm which column holds
the review date before building the drift-monitoring script.

Run:
    python check_columns.py
"""

import pandas as pd

df = pd.read_csv("processed/reviews_sentiment.csv", nrows=5)

print("Columns found:")
for col in df.columns:
    print(f"  - {col}")

print("\nFirst row as example:")
print(df.iloc[0])