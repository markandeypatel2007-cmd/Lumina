"""
drift_monitoring.py
---------------------
LUMINA Step 8 — Drift monitoring.

Uses the date-enabled datasets (reviews_sentiment.csv and
review_themes_v4.csv) to answer: "is anything getting worse over
time, and when did it start?"

Produces:
  1. processed/drift_overall_monthly.csv
     Month-by-month: total reviews, % negative, average rating.

  2. processed/drift_theme_monthly.csv
     Month-by-month, per theme: complaint count and share of all
     complaints that month.

  3. processed/drift_alerts.csv
     Automatic flags where a theme's monthly complaint share jumped
     by more than ALERT_THRESHOLD_PCT compared to the previous month.

Run:
    python drift_monitoring.py
"""

import pandas as pd
from pathlib import Path

SENTIMENT_FILE = "processed/reviews_sentiment.csv"
THEMES_FILE = "processed/review_themes_v4.csv"

OUT_OVERALL = "processed/drift_overall_monthly.csv"
OUT_THEME = "processed/drift_theme_monthly.csv"
OUT_ALERTS = "processed/drift_alerts.csv"

CHUNK_SIZE = 100_000

# Flag a theme if its share of total complaints changes by more than
# this many percentage points month-over-month.
ALERT_THRESHOLD_POINTS = 2.0

# Ignore alerts in months where there simply weren't enough total
# complaints for a percentage swing to mean anything (early years of
# this dataset have as few as 2-10 reviews in a month).
MIN_MONTHLY_COMPLAINTS_FOR_ALERT = 200


def month_bucket(series):
    """Convert reviewTime text (e.g. '09 17, 2014') to a YYYY-MM string."""
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.to_period("M").astype(str)


print("=" * 75)
print("LUMINA - STEP 8: DRIFT MONITORING")
print("=" * 75)

# ============================================================
# PART 1 — OVERALL SENTIMENT DRIFT (from the full sentiment file)
# ============================================================

print("\nBuilding overall monthly sentiment trend...")

overall_chunks = []

for chunk_num, chunk in enumerate(pd.read_csv(SENTIMENT_FILE, chunksize=CHUNK_SIZE), start=1):
    chunk["month"] = month_bucket(chunk["reviewTime"])
    chunk = chunk.dropna(subset=["month"])
    chunk = chunk[chunk["month"] != "NaT"]

    grouped = chunk.groupby("month").agg(
        review_count=("review", "count"),
        negative_count=("sentiment", lambda s: (s == "Negative").sum()),
        avg_rating=("rating", "mean"),
        avg_sentiment_score=("sentiment_score", "mean"),
    ).reset_index()

    overall_chunks.append(grouped)

    if chunk_num % 10 == 0:
        print(f"  ...processed {chunk_num * CHUNK_SIZE:,} rows so far")

overall = pd.concat(overall_chunks, ignore_index=True)

# Combine across chunks (same month can appear in multiple chunks)
overall_final = overall.groupby("month").apply(
    lambda g: pd.Series({
        "review_count": g["review_count"].sum(),
        "negative_count": g["negative_count"].sum(),
        "avg_rating": (g["avg_rating"] * g["review_count"]).sum() / g["review_count"].sum(),
        "avg_sentiment_score": (g["avg_sentiment_score"] * g["review_count"]).sum() / g["review_count"].sum(),
    }),
    include_groups=False
).reset_index()

overall_final["negative_pct"] = (
    overall_final["negative_count"] / overall_final["review_count"] * 100
).round(2)

# Flag months with too few reviews to be a reliable trend point
overall_final["low_volume"] = overall_final["review_count"] < MIN_MONTHLY_COMPLAINTS_FOR_ALERT

overall_final = overall_final.sort_values("month")
overall_final.to_csv(OUT_OVERALL, index=False)

print(f"Saved: {OUT_OVERALL}")
print(f"Months covered: {overall_final['month'].min()} to {overall_final['month'].max()}")

# ============================================================
# PART 2 — THEME DRIFT (from the theme-matched file)
# ============================================================

print("\nBuilding monthly theme trend...")

themes_df = pd.read_csv(THEMES_FILE)
themes_df["month"] = month_bucket(themes_df["reviewTime"])
themes_df = themes_df.dropna(subset=["month"])
themes_df = themes_df[themes_df["month"] != "NaT"]

theme_monthly = (
    themes_df.groupby(["month", "theme"])
    .size()
    .reset_index(name="complaint_count")
)

# Total complaints per month (all themes combined, for computing share)
month_totals = theme_monthly.groupby("month")["complaint_count"].sum().reset_index(
    name="month_total_complaints"
)

theme_monthly = theme_monthly.merge(month_totals, on="month")
theme_monthly["share_pct"] = (
    theme_monthly["complaint_count"] / theme_monthly["month_total_complaints"] * 100
).round(2)

theme_monthly = theme_monthly.sort_values(["theme", "month"])
theme_monthly.to_csv(OUT_THEME, index=False)

print(f"Saved: {OUT_THEME}")

# ============================================================
# PART 3 — DRIFT ALERTS
# ============================================================

print("\nChecking for drift alerts...")

alerts = []

for theme in theme_monthly["theme"].unique():
    theme_data = theme_monthly[theme_monthly["theme"] == theme].sort_values("month")
    theme_data = theme_data.reset_index(drop=True)

    for i in range(1, len(theme_data)):
        prev_share = theme_data.loc[i - 1, "share_pct"]
        curr_share = theme_data.loc[i, "share_pct"]
        prev_total = theme_data.loc[i - 1, "month_total_complaints"]
        curr_total = theme_data.loc[i, "month_total_complaints"]
        change = curr_share - prev_share

        # Skip low-volume months - a swing from 2 reviews to 3 reviews
        # can look like a huge percentage change but means nothing.
        if prev_total < MIN_MONTHLY_COMPLAINTS_FOR_ALERT or curr_total < MIN_MONTHLY_COMPLAINTS_FOR_ALERT:
            continue

        if abs(change) >= ALERT_THRESHOLD_POINTS:
            alerts.append({
                "month": theme_data.loc[i, "month"],
                "theme": theme,
                "previous_share_pct": prev_share,
                "current_share_pct": curr_share,
                "change_points": round(change, 2),
                "direction": "UP" if change > 0 else "DOWN",
                "month_total_complaints": curr_total,
            })

alerts_df = pd.DataFrame(alerts)
if len(alerts_df) > 0:
    alerts_df = alerts_df.sort_values("change_points", key=abs, ascending=False)
alerts_df.to_csv(OUT_ALERTS, index=False)

print(f"Saved: {OUT_ALERTS}")
print(f"Alerts found: {len(alerts_df):,}")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("DRIFT MONITORING COMPLETE")
print("=" * 75)

print("\nOverall monthly trend (last 12 months of data):")
print(overall_final.tail(12).to_string(index=False))

if len(alerts_df) > 0:
    print("\nTop 10 biggest month-over-month swings:")
    print(alerts_df.head(10).to_string(index=False))
else:
    print("\nNo significant drift alerts detected at this threshold.")

print("\nOutput files:")
print(f"  {OUT_OVERALL}")
print(f"  {OUT_THEME}")
print(f"  {OUT_ALERTS}")
print("\nSUCCESS!")