"""
theme_validation.py
--------------------
LUMINA Step 6 — Theme quality validation.

Problem: the Step 5 theme engine used some single-word keywords that are
too generic and can match unrelated content (e.g. "seller" appearing in
almost any review context, "light" meaning brightness OR weight, "key"
meaning a keyboard key in a totally unrelated complaint, "works" being
near-meaningless on its own).

This script:
  1. Uses a tightened keyword/phrase list per theme (ambiguous single
     words removed or replaced with more specific phrases).
  2. Re-runs complaint detection + theme classification on the full
     sentiment dataset (same definition as Step 5: VADER Negative OR
     rating <= 2), so results stay comparable but more precise.
  3. Builds a category x theme matrix, so you can see e.g. "Quality
     complaints are 91% Electronics, 6% Arts & Crafts, 3% Fashion".
  4. Saves a before/after comparison so you can show the validation
     step explicitly in your write-up (a real enterprise-grade touch).

Run:
    python theme_validation.py

This reprocesses the full dataset, so expect it to take a similar
amount of time to Step 5's theme_mapping.py run.
"""

import pandas as pd
import re
from pathlib import Path

INPUT_FILE = "processed/reviews_sentiment.csv"
OLD_SUMMARY_FILE = "processed/theme_summary_v3.csv"        # comparison only, note dataset size changed

OUTPUT_FILE = "processed/review_themes_v4.csv"
SUMMARY_FILE = "processed/theme_summary_v4.csv"
MATRIX_FILE = "processed/category_theme_matrix_v4.csv"
COMPARISON_FILE = "processed/theme_validation_comparison_v3_v4.csv"

CHUNK_SIZE = 50_000

print("=" * 75)
print("LUMINA - STEP 6: THEME QUALITY VALIDATION")
print("=" * 75)

# ============================================================
# REFINED THEME DEFINITIONS (v2)
# ------------------------------------------------------------
# Changes from v1, and why:
#   - Removed "seller" from Returns/Refunds: matches almost any
#     mention of the seller, not specifically a return/refund issue.
#   - Removed bare "light" from Size/Fit/Weight: ambiguous with
#     brightness/color. Replaced with "lightweight", "too light".
#   - Removed bare "key" from Usability/Setup: too often a literal
#     keyboard key in unrelated complaints. Kept "keys", "keypad".
#   - Removed bare "power" from Battery/Charging alone-standing use
#     is fine (power = battery power in context) but we tightened by
#     requiring word-boundary phrases like "power button", "power on",
#     "power off" alongside the original battery terms, and kept
#     "power" since it's rarely used in an unrelated sense in reviews.
#   - Removed "worth" from Price/Value on its own ("not worth it" is
#     common but "worth" alone catches too much); replaced with
#     "not worth", "worth it", "worth the price".
# ============================================================

THEMES = {

    "Battery / Charging": [
        "battery", "batteries", "charge", "charged",
        "charging", "power button", "power on", "power off",
        "backup battery", "battery life"
    ],

    "Quality / Durability": [
        "poor quality", "flimsy", "break", "broken", "broke",
        "damage", "damaged", "falling apart", "weak build",
        "not sturdy", "cheaply made", "cheap material",
        "stripped screw", "loose wires"
    ],

    "Technical / Performance": [
        "error", "fail", "failed", "failure", "doesn't work",
        "does not work", "stopped working", "performance issue",
        "malfunction", "driver issue", "software issue",
        "installation problem", "freezes", "crashes", "very slow"
    ],

    "Shipping / Delivery": [
        "shipping", "delivery", "delivered late",
        "arrived damaged", "arrived broken", "package damaged",
        "late arrival", "shipping delay"
    ],

    "Returns / Refunds": [
        "return", "returned", "returning", "refund",
        "replacement", "replace it", "money back", "refused refund"
    ],

    "Price / Value": [
        "overpriced", "too expensive", "not worth", "worth it",
        "worth the price", "waste of money", "cheaper elsewhere",
        "cost too much"
    ],

    "Audio / Sound": [
        "sound quality", "audio quality", "headset", "headphones",
        "low volume", "too much noise", "speaker", "speakers",
        "hurts ears", "sound cuts out"
    ],

    "Display / Image Quality": [
        "display quality", "screen quality", "blurry image",
        "poor picture", "bad picture", "dull colors",
        "washed out colors", "low brightness", "screen cracked",
        "picture quality", "image quality", "not sharp",
        "poor clarity", "clarity is poor", "quality of the picture",
        "screen didn't work", "screen did not work",
        "camera quality", "screen so dull", "images came out"
    ],

    "Connectivity": [
        "wifi", "wi-fi", "bluetooth", "won't connect",
        "keeps disconnecting", "connection drops", "poor reception",
        "gps not working", "weak signal"
    ],

    "Size / Fit / Weight": [
        "too small", "too big", "runs small", "runs large",
        "too tight", "too loose", "too heavy", "lightweight",
        "too light", "doesn't fit", "wrong size"
    ],

    "Missing / Incomplete Product": [
        "missing parts", "parts missing", "not included",
        "missing manual", "missing accessory", "missing accessories",
        "incomplete package", "doesn't include", "does not include",
        "missing the", "not included in the box"
    ],

    "Usability / Setup": [
        "hard to install", "installation problem", "setup issue",
        "confusing settings", "sticky keys", "keypad issue",
        "button stuck", "buttons stuck", "difficult to use",
        "not easy to use", "hard to use",
        "hard to navigate", "difficult to navigate",
        "pain to navigate", "settings not retained",
        "installation starts very slowly", "slow to install",
        "buried under menus"
    ]
}

# ============================================================
# COMPILE REGEX
# ============================================================

compiled_themes = {}

for theme, keywords in THEMES.items():
    patterns = []
    for keyword in keywords:
        # allow phrases to match with normal spacing, still word-bounded
        patterns.append(r"\b" + re.escape(keyword.lower()) + r"\b")
    compiled_themes[theme] = re.compile("|".join(patterns), re.IGNORECASE)

# ============================================================
# PROCESS REVIEWS
# ============================================================

print("\nProcessing full sentiment dataset with refined keywords...")
print(f"Chunk size: {CHUNK_SIZE:,}")

theme_rows = []

total_reviews = 0
complaint_reviews = 0
theme_matches = 0

reader = pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE)

for chunk_number, df in enumerate(reader, start=1):

    total_reviews += len(df)

    df["review_text"] = df["review"].fillna("").astype(str).str.lower()

    ratings = pd.to_numeric(df["rating"], errors="coerce")
    complaint_mask = (df["sentiment"] == "Negative") | (ratings <= 2)
    complaints = df[complaint_mask].copy()
    complaint_reviews += len(complaints)

    for theme, pattern in compiled_themes.items():
        mask = complaints["review_text"].str.contains(pattern, na=False, regex=True)
        matched = complaints[mask].copy()
        if len(matched) == 0:
            continue
        theme_matches += len(matched)
        matched["theme"] = theme
        theme_rows.append(
            matched[[
                "review", "rating", "category", "reviewTime", "unixReviewTime",
                "sentiment", "sentiment_score", "sentiment_confidence", "theme"
            ]]
        )

    print(f"Chunk {chunk_number:3d} | Reviews: {total_reviews:10,} | Complaints: {complaint_reviews:10,}")

# ============================================================
# COMBINE + DEDUPLICATE
# ============================================================

print("\n" + "=" * 75)
print("BUILDING VALIDATED THEME DATASET")
print("=" * 75)

result = pd.concat(theme_rows, ignore_index=True) if theme_rows else pd.DataFrame()

if len(result) > 0:
    result = result.drop_duplicates(subset=["review", "category", "theme"])

Path("processed").mkdir(exist_ok=True)
result.to_csv(OUTPUT_FILE, index=False)

# ============================================================
# THEME SUMMARY (v2)
# ============================================================

if len(result) > 0:
    summary = (
        result.groupby("theme")
        .agg(
            complaint_count=("review", "count"),
            average_rating=("rating", "mean"),
            average_sentiment=("sentiment_score", "mean"),
            average_confidence=("sentiment_confidence", "mean"),
            categories_affected=("category", "nunique"),
        )
        .reset_index()
    )

    summary["complaint_percentage"] = summary["complaint_count"] / complaint_reviews * 100

    def calculate_severity(row):
        if row["average_rating"] <= 2:
            return "HIGH"
        elif row["average_rating"] <= 3:
            return "MEDIUM"
        else:
            return "LOW"

    summary["severity"] = summary.apply(calculate_severity, axis=1)
    summary = summary.sort_values("complaint_count", ascending=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    # ============================================================
    # CATEGORY x THEME MATRIX
    # ============================================================
    matrix = pd.crosstab(result["theme"], result["category"])
    matrix["Total"] = matrix.sum(axis=1)
    matrix = matrix.sort_values("Total", ascending=False)
    matrix.to_csv(MATRIX_FILE)

    # As percentages within each theme (row-normalized), easier to read
    matrix_pct = pd.crosstab(result["theme"], result["category"], normalize="index") * 100
    matrix_pct = matrix_pct.round(1)
    matrix_pct.to_csv("processed/category_theme_matrix_v4_pct.csv")

# ============================================================
# BEFORE / AFTER COMPARISON
# ============================================================

if Path(OLD_SUMMARY_FILE).exists() and len(result) > 0:
    old_summary = pd.read_csv(OLD_SUMMARY_FILE)[["theme", "complaint_count"]]
    old_summary = old_summary.rename(columns={"complaint_count": "complaint_count_v3"})

    new_summary = summary[["theme", "complaint_count"]].rename(
        columns={"complaint_count": "complaint_count_v4"}
    )

    comparison = old_summary.merge(new_summary, on="theme", how="outer").fillna(0)
    comparison["change"] = comparison["complaint_count_v4"] - comparison["complaint_count_v3"]
    comparison["pct_change"] = (
        comparison["change"] / comparison["complaint_count_v3"].replace(0, pd.NA) * 100
    ).round(1)
    comparison = comparison.sort_values("theme")
    comparison.to_csv(COMPARISON_FILE, index=False)

    print("\n" + "=" * 75)
    print("BEFORE (v3, 5.9M reviews) vs AFTER (v4, 6.8M reviews with dates)")
    print("NOTE: same keywords as v3 - any change here is from the larger")
    print("dataset (real JSON source), not from keyword changes.")
    print("=" * 75)
    print(comparison.to_string(index=False))

# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 75)
print("VALIDATION COMPLETE")
print("=" * 75)

print(f"\nTotal reviews processed:   {total_reviews:,}")
print(f"Complaint reviews found:   {complaint_reviews:,}")
print(f"Theme matches (v4):        {theme_matches:,}")

if len(result) > 0:
    print("\n" + "=" * 75)
    print("TOP COMPLAINT THEMES (v4 — with dates)")
    print("=" * 75)
    print(
        summary[[
            "theme", "complaint_count", "complaint_percentage",
            "average_rating", "average_sentiment", "severity"
        ]].head(20).to_string(index=False)
    )

    print("\n" + "=" * 75)
    print("CATEGORY x THEME MATRIX (counts)")
    print("=" * 75)
    print(matrix.to_string())

print("\nOutput files:")
print(f"  {OUTPUT_FILE}")
print(f"  {SUMMARY_FILE}")
print(f"  {MATRIX_FILE}")
print("  processed/category_theme_matrix_pct.csv")
print(f"  {COMPARISON_FILE}")

print("\nSUCCESS!")