import pandas as pd
import re
from pathlib import Path

INPUT_FILE = "processed/reviews_sentiment.csv"
OUTPUT_FILE = "processed/review_themes.csv"
SUMMARY_FILE = "processed/theme_summary.csv"

CHUNK_SIZE = 50_000

print("=" * 75)
print("LUMINA - FULL-SCALE ENTERPRISE COMPLAINT THEME ANALYSIS")
print("=" * 75)

# ============================================================
# THEME DEFINITIONS
# ============================================================

THEMES = {

    "Battery / Charging": [
        "battery", "batteries", "charge", "charged",
        "charging", "power", "backup"
    ],

    "Quality / Durability": [
        "quality", "poor quality", "flimsy", "break",
        "broken", "broke", "damage", "damaged",
        "apart", "weak", "sturdy", "solid",
        "screw", "wires"
    ],

    "Technical / Performance": [
        "error", "fail", "failed", "failure", "fix",
        "performance", "function", "driver", "drivers",
        "software", "installation", "setting", "settings",
        "slow", "freeze", "crash"
    ],

    "Shipping / Delivery": [
        "shipping", "delivery", "delivered",
        "arrived", "arrival", "package", "parcel"
    ],

    "Returns / Refunds": [
        "return", "returned", "returning",
        "refund", "replacement", "replace",
        "seller", "money back"
    ],

    "Price / Value": [
        "price", "expensive", "cheap", "cheaper",
        "cost", "worth", "value", "paid", "spend"
    ],

    "Audio / Sound": [
        "sound", "sounds", "audio", "headset",
        "headphones", "volume", "noise", "speaker",
        "speakers", "ears"
    ],

    "Display / Image Quality": [
        "display", "screen", "image", "images",
        "photo", "photos", "picture", "pictures",
        "colors", "colour", "brightness"
    ],

    "Connectivity": [
        "wifi", "wi-fi", "bluetooth", "connection",
        "connect", "connected", "disconnect",
        "reception", "gps", "signal"
    ],

    "Size / Fit / Weight": [
        "size", "smaller", "small", "larger",
        "large", "tight", "loose", "weight",
        "heavy", "light", "feet"
    ],

    "Missing / Incomplete Product": [
        "missing", "included", "include",
        "parts", "manual", "supply",
        "accessory", "accessories"
    ],

    "Usability / Setup": [
        "manual", "installation", "setup",
        "setting", "settings", "keys",
        "key", "touch", "button", "buttons",
        "easy to use", "difficult"
    ]
}

# ============================================================
# COMPILE REGEX
# ============================================================

compiled_themes = {}

for theme, keywords in THEMES.items():

    patterns = []

    for keyword in keywords:
        patterns.append(
            r"\b" + re.escape(keyword.lower()) + r"\b"
        )

    compiled_themes[theme] = re.compile(
        "|".join(patterns),
        re.IGNORECASE
    )

# ============================================================
# PROCESS REVIEWS
# ============================================================

print("\nProcessing full sentiment dataset...")
print(f"Chunk size: {CHUNK_SIZE:,}")

first_write = True

theme_rows = []

total_reviews = 0
complaint_reviews = 0
theme_matches = 0

reader = pd.read_csv(
    INPUT_FILE,
    chunksize=CHUNK_SIZE
)

for chunk_number, df in enumerate(reader, start=1):

    total_reviews += len(df)

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    df["review_text"] = (
        df["review"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    # --------------------------------------------------------
    # COMPLAINT DEFINITION
    # --------------------------------------------------------
    #
    # We use BOTH:
    #
    # 1. VADER Negative
    # 2. Rating <= 2
    #
    # This improves complaint recall compared with relying
    # exclusively on VADER.
    # --------------------------------------------------------

    ratings = pd.to_numeric(
        df["rating"],
        errors="coerce"
    )

    complaint_mask = (
        (df["sentiment"] == "Negative") |
        (ratings <= 2)
    )

    complaints = df[complaint_mask].copy()

    complaint_reviews += len(complaints)

    # --------------------------------------------------------
    # THEME MATCHING
    # --------------------------------------------------------

    for theme, pattern in compiled_themes.items():

        mask = complaints["review_text"].str.contains(
            pattern,
            na=False,
            regex=True
        )

        matched = complaints[mask].copy()

        if len(matched) == 0:
            continue

        theme_matches += len(matched)

        matched["theme"] = theme

        # Keep useful fields
        theme_rows.append(
            matched[
                [
                    "review",
                    "rating",
                    "category",
                    "sentiment",
                    "sentiment_score",
                    "sentiment_confidence",
                    "theme"
                ]
            ]
        )

    print(
        f"Chunk {chunk_number:3d} | "
        f"Reviews: {total_reviews:10,} | "
        f"Complaints: {complaint_reviews:10,}"
    )

# ============================================================
# COMBINE RESULTS
# ============================================================

print("\n" + "=" * 75)
print("BUILDING THEME DATASET")
print("=" * 75)

if theme_rows:

    result = pd.concat(
        theme_rows,
        ignore_index=True
    )

else:

    result = pd.DataFrame()

# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

if len(result) > 0:

    result = result.drop_duplicates(
        subset=[
            "review",
            "category",
            "theme"
        ]
    )

# ============================================================
# SAVE THEME DATASET
# ============================================================

Path("processed").mkdir(
    exist_ok=True
)

result.to_csv(
    OUTPUT_FILE,
    index=False
)

# ============================================================
# THEME SUMMARY
# ============================================================

if len(result) > 0:

    summary = (
        result
        .groupby("theme")
        .agg(
            complaint_count=("review", "count"),
            average_rating=("rating", "mean"),
            average_sentiment=("sentiment_score", "mean"),
            average_confidence=("sentiment_confidence", "mean"),
            categories_affected=("category", "nunique")
        )
        .reset_index()
    )

    summary["complaint_percentage"] = (
        summary["complaint_count"]
        / complaint_reviews
        * 100
    )

    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    def calculate_severity(row):

        rating = row["average_rating"]

        if rating <= 2:
            return "HIGH"

        elif rating <= 3:
            return "MEDIUM"

        else:
            return "LOW"

    summary["severity"] = summary.apply(
        calculate_severity,
        axis=1
    )

    summary = summary.sort_values(
        "complaint_count",
        ascending=False
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 75)
print("ANALYSIS COMPLETE")
print("=" * 75)

print(f"\nTotal reviews processed:     {total_reviews:,}")
print(f"Complaint reviews found:    {complaint_reviews:,}")
print(f"Theme matches:               {theme_matches:,}")

if len(result) > 0:

    print("\n" + "=" * 75)
    print("TOP COMPLAINT THEMES")
    print("=" * 75)

    print(
        summary[
            [
                "theme",
                "complaint_count",
                "complaint_percentage",
                "average_rating",
                "average_sentiment",
                "severity"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

print("\nOutput files:")
print(f"  {OUTPUT_FILE}")
print(f"  {SUMMARY_FILE}")

print("\nSUCCESS!")