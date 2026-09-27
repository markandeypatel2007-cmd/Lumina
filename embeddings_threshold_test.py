"""
embeddings_threshold_test.py
------------------------------
LUMINA - ML upgrade, step 1: calibrate the embeddings approach.

Instead of keyword matching, this uses a pretrained sentence-embedding
model to compare each review against a natural-language description
of each theme, and assigns themes by semantic similarity.

Before running this on the full 1.3M complaint reviews (which takes a
while), this script tests it on a small sample of 3,000 reviews at a
few different similarity thresholds, so we can see what threshold
gives sensible results before committing to the full run.

First-time setup (only needed once):
    pip install sentence-transformers

Run:
    python embeddings_threshold_test.py

The first run will also download a small (~90MB) pretrained model
automatically - this needs internet access once, then it's cached
locally.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

print("=" * 75)
print("LUMINA - EMBEDDINGS THEME DETECTION - THRESHOLD CALIBRATION")
print("=" * 75)

# ============================================================
# THEME DESCRIPTIONS (natural language, not keywords)
# ============================================================

THEME_DESCRIPTIONS = {
    "Battery / Charging": "The battery drains quickly, does not hold a charge, or the charging function is broken.",
    "Quality / Durability": "The product feels cheaply made, broke, or fell apart after normal use.",
    "Technical / Performance": "The device has technical errors, crashes, freezes, or fails to function properly.",
    "Shipping / Delivery": "The package arrived late, damaged, or was lost during shipping.",
    "Returns / Refunds": "The customer wants to return the product or requests a refund from the seller.",
    "Price / Value": "The product is overpriced or not worth the money paid.",
    "Audio / Sound": "The sound quality is poor, too quiet, distorted, or the audio device is uncomfortable.",
    "Display / Image Quality": "The screen or picture quality is blurry, dim, or otherwise poor.",
    "Connectivity": "The device has trouble connecting via Bluetooth or WiFi, or has a weak signal.",
    "Size / Fit / Weight": "The product is the wrong size, does not fit properly, or is too heavy or light.",
    "Missing / Incomplete Product": "The product arrived with missing parts, accessories, or incomplete contents.",
    "Usability / Setup": "The product is difficult to set up, install, or use, with confusing controls or instructions.",
}

print("\nLoading embedding model (first run downloads ~90MB, then cached)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

theme_names = list(THEME_DESCRIPTIONS.keys())
theme_texts = list(THEME_DESCRIPTIONS.values())
theme_embeddings = model.encode(theme_texts, normalize_embeddings=True)

# ============================================================
# LOAD A SAMPLE OF COMPLAINT REVIEWS
# ============================================================

print("\nLoading a sample of complaint reviews...")

df = pd.read_csv("processed/reviews_sentiment.csv")
ratings = pd.to_numeric(df["rating"], errors="coerce")
complaints = df[(df["sentiment"] == "Negative") | (ratings <= 2)].copy()

sample = complaints.sample(n=min(3000, len(complaints)), random_state=42).reset_index(drop=True)
print(f"Sample size: {len(sample):,} complaint reviews")

# ============================================================
# EMBED THE SAMPLE
# ============================================================

print("\nEncoding sample reviews (this takes a moment)...")
review_texts = sample["review"].fillna("").astype(str).tolist()
review_embeddings = model.encode(review_texts, normalize_embeddings=True, show_progress_bar=True)

# Cosine similarity (since embeddings are normalized, this is just a dot product)
similarity_matrix = review_embeddings @ theme_embeddings.T  # shape: (n_reviews, n_themes)

# ============================================================
# TEST DIFFERENT THRESHOLDS
# ============================================================

print("\n" + "=" * 75)
print("THRESHOLD COMPARISON")
print("=" * 75)

for threshold in [0.25, 0.30, 0.35, 0.40, 0.45]:
    matches_per_review = (similarity_matrix >= threshold).sum(axis=1)
    zero_matches = (matches_per_review == 0).sum()
    avg_matches = matches_per_review.mean()

    print(f"\nThreshold {threshold}:")
    print(f"  Reviews with 0 themes matched: {zero_matches:,} ({zero_matches/len(sample)*100:.1f}%)")
    print(f"  Average themes matched per review: {avg_matches:.2f}")

# ============================================================
# SHOW EXAMPLE MATCHES AT THRESHOLD 0.35 (a reasonable starting point)
# ============================================================

TEST_THRESHOLD = 0.35

print("\n" + "=" * 75)
print(f"EXAMPLE MATCHES AT THRESHOLD {TEST_THRESHOLD}")
print("=" * 75)
print("(Read these and judge: do the assigned themes make sense?)\n")

for i in range(15):
    text = review_texts[i]
    if len(text) > 200:
        text = text[:200] + "..."

    matched_themes = [
        (theme_names[j], round(float(similarity_matrix[i, j]), 3))
        for j in range(len(theme_names))
        if similarity_matrix[i, j] >= TEST_THRESHOLD
    ]
    matched_themes.sort(key=lambda x: -x[1])

    print(f"[{i+1}] Rating: {sample.loc[i, 'rating']} | {text}")
    if matched_themes:
        print(f"    Matched: {matched_themes}")
    else:
        print(f"    Matched: (none)")
    print()

print("=" * 75)
print("Look at the threshold comparison and the example matches above.")
print("Pick a threshold where: few reviews get 0 themes, average themes")
print("per review is reasonable (not 8+), and the example matches look")
print("correct. Tell me which threshold looks best and we'll run the")
print("full 1.3M-review job with it.")
print("=" * 75)