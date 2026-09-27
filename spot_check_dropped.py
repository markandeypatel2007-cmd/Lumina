"""
spot_check_dropped.py
----------------------
LUMINA Step 6b — Sanity check on the theme validation.

Some themes lost 95%+ of their matches when we tightened the keywords
(Display/Image Quality, Usability/Setup, Missing/Incomplete Product).
That could mean the old keywords were mostly noise (good), or it could
mean the new phrases are too narrow and we're losing real complaints
(bad). The only way to know is to actually read a sample.

This script pulls a random sample of reviews that matched a theme in
v1 (the broad keyword version) but did NOT match in v2 (the tightened
version), for the themes with the biggest drops. Read through the
printed samples and judge: are these mostly irrelevant/false matches,
or are some of them genuine complaints we're now missing?

Run:
    python spot_check_dropped.py
"""

import pandas as pd

V1_FILE = "processed/review_themes.csv"
V2_FILE = "processed/review_themes_v2.csv"

# Themes with the largest drops - the ones most worth checking
THEMES_TO_CHECK = [
    "Display / Image Quality",
    "Usability / Setup",
    "Missing / Incomplete Product",
]

SAMPLE_SIZE = 15  # how many dropped reviews to print per theme

print("Loading v1 and v2 theme results...")
v1 = pd.read_csv(V1_FILE)
v2 = pd.read_csv(V2_FILE)

for theme in THEMES_TO_CHECK:
    print("\n" + "=" * 90)
    print(f"THEME: {theme}")
    print("=" * 90)

    v1_theme = v1[v1["theme"] == theme]
    v2_theme = v2[v2["theme"] == theme]

    # Reviews that matched in v1 but not in v2 (i.e. dropped by the tightening)
    dropped = v1_theme[~v1_theme["review"].isin(v2_theme["review"])]

    print(f"v1 matches: {len(v1_theme):,}  |  v2 matches: {len(v2_theme):,}  |  Dropped: {len(dropped):,}")

    if len(dropped) == 0:
        print("(Nothing was dropped for this theme.)")
        continue

    sample = dropped.sample(n=min(SAMPLE_SIZE, len(dropped)), random_state=42)

    for i, row in enumerate(sample.itertuples(), start=1):
        text = str(row.review)
        if len(text) > 300:
            text = text[:300] + "..."
        print(f"\n[{i}] Rating: {row.rating} | Category: {row.category}")
        print(f"    {text}")

print("\n" + "=" * 90)
print("Read through the samples above for each theme.")
print("For each one, judge: are these mostly NOT actually about that theme")
print("(good - the tightening was correct), or do some genuinely belong")
print("(bad - we may need to add back a keyword/phrase we removed)?")
print("=" * 90)