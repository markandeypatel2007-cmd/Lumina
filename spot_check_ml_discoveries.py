"""
spot_check_ml_discoveries.py
-------------------------------
Reads a sample of reviews the ML classifier flagged for a theme that
the keyword approach did NOT catch, so we can manually verify these
are genuine complaints and not false positives - same instinct as
checking the keyword theme validation earlier in this project.

Run:
    python spot_check_ml_discoveries.py
"""

import pandas as pd

ml_df = pd.read_csv("processed/review_themes_ml.csv")
keyword_df = pd.read_csv("processed/review_themes_v4.csv")

# Check one high-precision theme and one lower-precision theme
THEMES_TO_CHECK = ["Audio / Sound", "Usability / Setup"]
SAMPLE_SIZE = 15

for theme in THEMES_TO_CHECK:
    print("=" * 90)
    print(f"THEME: {theme}")
    print("=" * 90)

    ml_theme = ml_df[ml_df["theme"] == theme]
    keyword_theme_reviews = set(keyword_df[keyword_df["theme"] == theme]["review"].astype(str))

    # Reviews ML flagged that keyword-matching never caught
    discovered = ml_theme[~ml_theme["review"].astype(str).isin(keyword_theme_reviews)]

    print(f"ML discovered (not caught by keywords): {len(discovered):,}\n")

    sample = discovered.sample(n=min(SAMPLE_SIZE, len(discovered)), random_state=1)

    for i, row in enumerate(sample.itertuples(), start=1):
        text = str(row.review)
        if len(text) > 250:
            text = text[:250] + "..."
        print(f"[{i}] Rating: {row.rating} | Confidence: {row.ml_confidence:.3f}")
        print(f"    {text}\n")

print("=" * 90)
print("For each sample above, judge: is this genuinely about that theme?")
print("Compare the high-precision theme (Audio/Sound) against the lower-")
print("precision one (Usability/Setup) - expect the first to look cleaner.")
print("=" * 90)