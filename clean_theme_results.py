"""
clean_theme_results.py
-------------------------
Fixes a specific contamination issue found during spot-checking: some
reviews with 4-5 star ratings got labeled "Negative" by VADER sentiment
(likely due to mixed or sarcastic phrasing VADER misreads), and those
got treated as "complaints" everywhere downstream - polluting both the
keyword-based themes AND the ML classifier's training data and results.

A genuine complaint essentially never comes with a 4-5 star rating, so
this removes those rows directly - a fast, targeted fix instead of
re-running the expensive sentiment/theme/classifier pipeline.

Run:
    python clean_theme_results.py
"""

import pandas as pd

MAX_RATING_FOR_COMPLAINT = 3  # ratings above this are not treated as complaints

print("=" * 75)
print("LUMINA - CLEANING CONTAMINATED COMPLAINT DATA")
print("=" * 75)

# ============================================================
# CLEAN KEYWORD-BASED THEMES (v4)
# ============================================================

print("\nCleaning keyword-based theme results (v4)...")
keyword_df = pd.read_csv("processed/review_themes_v4.csv")
before = len(keyword_df)
keyword_clean = keyword_df[keyword_df["rating"] <= MAX_RATING_FOR_COMPLAINT].copy()
after = len(keyword_clean)
print(f"  Removed {before - after:,} rows with rating > {MAX_RATING_FOR_COMPLAINT} ({(before-after)/before*100:.1f}%)")
keyword_clean.to_csv("processed/review_themes_v4_clean.csv", index=False)

# ============================================================
# CLEAN ML CLASSIFIER RESULTS
# ============================================================

print("\nCleaning ML classifier results...")
ml_df = pd.read_csv("processed/review_themes_ml.csv")
before = len(ml_df)
ml_clean = ml_df[ml_df["rating"] <= MAX_RATING_FOR_COMPLAINT].copy()
after = len(ml_clean)
print(f"  Removed {before - after:,} rows with rating > {MAX_RATING_FOR_COMPLAINT} ({(before-after)/before*100:.1f}%)")
ml_clean.to_csv("processed/review_themes_ml_clean.csv", index=False)

# ============================================================
# SHOW WHICH THEMES WERE MOST AFFECTED
# ============================================================

print("\n" + "=" * 75)
print("IMPACT BY THEME (ML results)")
print("=" * 75)

before_counts = ml_df.groupby("theme").size().rename("before")
after_counts = ml_clean.groupby("theme").size().rename("after")
impact = pd.concat([before_counts, after_counts], axis=1)
impact["removed"] = impact["before"] - impact["after"]
impact["removed_pct"] = (impact["removed"] / impact["before"] * 100).round(1)
impact = impact.sort_values("removed_pct", ascending=False)

print(impact.to_string())

# ============================================================
# REBUILD SUMMARIES ON CLEANED DATA
# ============================================================

print("\nRebuilding theme summaries on cleaned data...")

ml_summary = (
    ml_clean.groupby("theme")
    .agg(
        complaint_count=("review", "count"),
        average_rating=("rating", "mean"),
        average_confidence=("ml_confidence", "mean"),
    )
    .reset_index()
    .sort_values("complaint_count", ascending=False)
)
ml_summary.to_csv("processed/theme_summary_ml_clean.csv", index=False)

keyword_summary = (
    keyword_clean.groupby("theme")
    .agg(
        complaint_count=("review", "count"),
        average_rating=("rating", "mean"),
    )
    .reset_index()
    .sort_values("complaint_count", ascending=False)
)
keyword_summary.to_csv("processed/theme_summary_v4_clean.csv", index=False)

# ============================================================
# REBUILD ML vs KEYWORD COMPARISON ON CLEANED DATA
# ============================================================

print("\nRebuilding ML vs keyword comparison on cleaned data...")

all_themes = sorted(set(keyword_clean["theme"].unique()) | set(ml_clean["theme"].unique()))
comparison_rows = []

for theme in all_themes:
    keyword_reviews = set(keyword_clean[keyword_clean["theme"] == theme]["review"].astype(str))
    ml_reviews = set(ml_clean[ml_clean["theme"] == theme]["review"].astype(str))

    both = keyword_reviews & ml_reviews
    ml_only = ml_reviews - keyword_reviews
    keyword_only = keyword_reviews - ml_reviews

    comparison_rows.append({
        "theme": theme,
        "keyword_count": len(keyword_reviews),
        "ml_count": len(ml_reviews),
        "agree_both": len(both),
        "ml_discovered_new": len(ml_only),
        "keyword_only_missed_by_ml": len(keyword_only),
    })

comparison_df = pd.DataFrame(comparison_rows).sort_values("ml_discovered_new", ascending=False)
comparison_df.to_csv("processed/ml_vs_keyword_comparison_clean.csv", index=False)

print(comparison_df.to_string(index=False))

total_discovered = comparison_df["ml_discovered_new"].sum()
print(f"\nTotal NEW complaints discovered by AI (after cleaning): {total_discovered:,}")

print("\nOutput files:")
print("  processed/review_themes_v4_clean.csv")
print("  processed/review_themes_ml_clean.csv")
print("  processed/theme_summary_v4_clean.csv")
print("  processed/theme_summary_ml_clean.csv")
print("  processed/ml_vs_keyword_comparison_clean.csv")

print("\nSUCCESS!")