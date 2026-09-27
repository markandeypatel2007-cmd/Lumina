"""
apply_theme_classifier_full.py
---------------------------------
LUMINA - ML upgrade, step 3: apply the trained classifier to the
full complaint dataset (~1.3M reviews).

This is a long-running job (roughly 9-10 hours based on the encoding
speed seen during training) - designed to run overnight:
  - Writes results incrementally (chunk by chunk), so if it's
    interrupted, you keep everything processed so far.
  - Prints progress with elapsed time and an ETA after the first
    few chunks, so you can check on it.

Produces:
  processed/review_themes_ml.csv
      One row per (review, theme) match from the ML classifier -
      same format as review_themes_v4.csv, so the dashboard and
      existing analysis code can use either one.

  processed/theme_summary_ml.csv
      Per-theme counts/stats from the ML classifier.

  processed/ml_vs_keyword_comparison.csv
      For each theme: how many complaints the keyword approach found,
      how many the ML approach found, how many they agree on, and -
      the key hackathon number - how many genuine complaints the ML
      model caught that the keyword approach completely missed.

Run:
    python apply_theme_classifier_full.py

Let this run overnight or in the background - it prints progress as
it goes, so you can check on it any time without needing to wait at
the terminal.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path
import time

SENTIMENT_FILE = "processed/reviews_sentiment.csv"
KEYWORD_THEMES_FILE = "processed/review_themes_v4.csv"
MODEL_FILE = "models/theme_classifiers.pkl"

OUTPUT_FILE = Path("processed/review_themes_ml.csv")
SUMMARY_FILE = "processed/theme_summary_ml.csv"
COMPARISON_FILE = "processed/ml_vs_keyword_comparison.csv"

CHUNK_SIZE = 20_000
BATCH_SIZE = 64

print("=" * 75)
print("LUMINA - APPLYING ML CLASSIFIER TO FULL COMPLAINT DATASET")
print("=" * 75)

# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading trained classifiers...")
with open(MODEL_FILE, "rb") as f:
    saved = pickle.load(f)

classifiers = saved["classifiers"]
all_themes = saved["themes"]
thresholds = saved.get("thresholds", {theme: 0.5 for theme in all_themes})

print(f"Loaded {len(classifiers)} classifiers with tuned thresholds:")
for theme in all_themes:
    if theme in thresholds:
        print(f"  {theme}: threshold = {thresholds[theme]:.3f}")

print("\nLoading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# ============================================================
# PREPARE OUTPUT FILE
# ============================================================

if OUTPUT_FILE.exists():
    print(f"\nRemoving old {OUTPUT_FILE} to start fresh...")
    OUTPUT_FILE.unlink()

first_write = True

# ============================================================
# PROCESS IN CHUNKS
# ============================================================

print("\nProcessing full complaint dataset (this will take several hours)...")
print(f"Chunk size: {CHUNK_SIZE:,}\n")

start_time = time.time()
total_reviews = 0
total_complaints = 0
total_theme_matches = 0
theme_match_counts = {theme: 0 for theme in all_themes}

for chunk_num, chunk in enumerate(pd.read_csv(SENTIMENT_FILE, chunksize=CHUNK_SIZE), start=1):

    total_reviews += len(chunk)

    ratings = pd.to_numeric(chunk["rating"], errors="coerce")
    complaints = chunk[(chunk["sentiment"] == "Negative") | (ratings <= 2)].copy()

    if len(complaints) == 0:
        continue

    total_complaints += len(complaints)

    texts = complaints["review"].fillna("").astype(str).tolist()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=BATCH_SIZE, show_progress_bar=False)

    output_rows = []

    for theme in all_themes:
        if theme not in classifiers:
            continue
        clf = classifiers[theme]
        threshold = thresholds.get(theme, 0.5)

        probs = clf.predict_proba(embeddings)[:, 1]
        matched_mask = probs >= threshold

        if matched_mask.sum() == 0:
            continue

        matched = complaints[matched_mask].copy()
        matched["theme"] = theme
        matched["ml_confidence"] = probs[matched_mask]

        theme_match_counts[theme] += len(matched)
        total_theme_matches += len(matched)

        output_rows.append(matched[[
            "review", "rating", "category", "reviewTime", "unixReviewTime",
            "sentiment", "sentiment_score", "sentiment_confidence", "theme", "ml_confidence"
        ]])

    if output_rows:
        chunk_result = pd.concat(output_rows, ignore_index=True)
        chunk_result.to_csv(
            OUTPUT_FILE, mode="w" if first_write else "a",
            header=first_write, index=False
        )
        first_write = False

    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60
    reviews_per_sec = total_reviews / elapsed if elapsed > 0 else 0

    # Rough ETA based on progress so far
    remaining_rows = None
    eta_str = ""
    if chunk_num >= 3 and reviews_per_sec > 0:
        # We don't know exact total row count in advance from a streaming read,
        # but we know it's about 6.79M based on earlier pipeline runs
        approx_total = 6_794_913
        remaining_rows = max(approx_total - total_reviews, 0)
        eta_min = remaining_rows / reviews_per_sec / 60
        eta_str = f" | ETA: {eta_min:.0f} min remaining"

    print(
        f"Chunk {chunk_num:>4} | Reviews: {total_reviews:>10,} | "
        f"Complaints: {total_complaints:>9,} | Theme matches: {total_theme_matches:>9,} | "
        f"Elapsed: {elapsed_min:.1f} min{eta_str}"
    )

# ============================================================
# FINAL SUMMARY
# ============================================================

elapsed_total = (time.time() - start_time) / 60

print("\n" + "=" * 75)
print("ML CLASSIFICATION COMPLETE")
print("=" * 75)
print(f"Total reviews processed:   {total_reviews:,}")
print(f"Total complaints found:    {total_complaints:,}")
print(f"Total theme matches:       {total_theme_matches:,}")
print(f"Total time:                {elapsed_total:.1f} minutes")

# Build summary CSV
summary_rows = []
for theme, count in theme_match_counts.items():
    summary_rows.append({
        "theme": theme,
        "ml_complaint_count": count,
        "ml_complaint_percentage": round(count / total_complaints * 100, 2) if total_complaints > 0 else 0,
    })
summary_df = pd.DataFrame(summary_rows).sort_values("ml_complaint_count", ascending=False)
summary_df.to_csv(SUMMARY_FILE, index=False)

print("\nML theme counts:")
print(summary_df.to_string(index=False))

# ============================================================
# COMPARE AGAINST KEYWORD-BASED APPROACH
# ============================================================

print("\n" + "=" * 75)
print("COMPARING ML RESULTS AGAINST KEYWORD-BASED APPROACH (v4)")
print("=" * 75)

keyword_df = pd.read_csv(KEYWORD_THEMES_FILE)
ml_df = pd.read_csv(OUTPUT_FILE)

comparison_rows = []

for theme in all_themes:
    keyword_reviews = set(keyword_df[keyword_df["theme"] == theme]["review"].astype(str))
    ml_reviews = set(ml_df[ml_df["theme"] == theme]["review"].astype(str))

    both = keyword_reviews & ml_reviews
    ml_only = ml_reviews - keyword_reviews          # AI found, keywords missed
    keyword_only = keyword_reviews - ml_reviews      # keywords found, AI missed

    comparison_rows.append({
        "theme": theme,
        "keyword_count": len(keyword_reviews),
        "ml_count": len(ml_reviews),
        "agree_both": len(both),
        "ml_discovered_new": len(ml_only),
        "keyword_only_missed_by_ml": len(keyword_only),
    })

comparison_df = pd.DataFrame(comparison_rows).sort_values("ml_discovered_new", ascending=False)
comparison_df.to_csv(COMPARISON_FILE, index=False)

print(comparison_df.to_string(index=False))

total_discovered = comparison_df["ml_discovered_new"].sum()
print(f"\nTotal NEW complaints discovered by AI that keyword-matching missed: {total_discovered:,}")

print("\nOutput files:")
print(f"  {OUTPUT_FILE}")
print(f"  {SUMMARY_FILE}")
print(f"  {COMPARISON_FILE}")

print("\nSUCCESS!")