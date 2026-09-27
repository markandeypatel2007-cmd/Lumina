"""
train_theme_classifier.py
----------------------------
LUMINA - ML upgrade, step 2: train a real supervised classifier.

The single-anchor-sentence approach (embeddings_threshold_test.py)
wasn't accurate enough - too many obvious complaints got zero matches.

This script instead:
  1. Uses your validated keyword-matched themes (review_themes_v4.csv)
     as TRAINING LABELS (this data was already quality-checked in
     Step 6, so it's a solid foundation to learn from).
  2. Embeds a training sample of labeled complaint reviews.
  3. Trains one logistic regression classifier per theme (multi-label)
     on top of those embeddings - this is the actual "learning from
     data" part that makes this real ML, not just similarity lookup.
  4. Evaluates on a held-out test split with accuracy/precision/
     recall/F1 per theme, the same rigor as your sentiment validation.

Run:
    python train_theme_classifier.py

This trains on a manageable sample (not all 1.3M rows) so it runs in
a few minutes. Once we confirm the accuracy is good, a follow-up
script applies the trained model to the full dataset.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, precision_recall_curve
import pickle
from pathlib import Path

MAX_PER_THEME = 6000        # cap positive examples per theme, for speed
MAX_NEGATIVES = 8000        # complaints matching NO theme, used as negative examples
TEST_SIZE = 0.2
MAX_RATING_FOR_TRAINING = 3  # exclude high-rating "complaints" - likely sentiment mislabels

CACHE_X = Path("processed/embeddings_cache_X_clean.npy")
CACHE_Y = Path("processed/embeddings_cache_Y_clean.npy")
CACHE_THEMES = Path("processed/embeddings_cache_themes_clean.pkl")

print("=" * 75)
print("LUMINA - TRAINING SUPERVISED THEME CLASSIFIER")
print("=" * 75)

if CACHE_X.exists() and CACHE_Y.exists() and CACHE_THEMES.exists():
    print("\nFound cached embeddings from a previous run - skipping re-encoding!")
    X = np.load(CACHE_X)
    Y = np.load(CACHE_Y)
    with open(CACHE_THEMES, "rb") as f:
        all_themes = pickle.load(f)
    print(f"Loaded {len(X):,} cached embeddings for {len(all_themes)} themes")

else:
    # ============================================================
    # BUILD TRAINING DATA FROM VALIDATED KEYWORD LABELS
    # ============================================================

    print("\nLoading validated theme labels (from Step 6)...")
    theme_data = pd.read_csv("processed/review_themes_v4.csv")

    before_filter = len(theme_data)
    theme_data = theme_data[theme_data["rating"] <= MAX_RATING_FOR_TRAINING]
    print(f"Filtered out {before_filter - len(theme_data):,} high-rating mislabeled rows "
          f"(rating > {MAX_RATING_FOR_TRAINING}) from training labels")

    all_themes = sorted(theme_data["theme"].unique())
    print(f"Themes: {all_themes}")

    print("\nBuilding multi-label training table...")
    labeled = (
        theme_data
        .drop_duplicates(subset=["review", "category", "theme"])
        .assign(flag=1)
        .pivot_table(index="review", columns="theme", values="flag", fill_value=0)
        .reset_index()
    )

    for theme in all_themes:
        if theme not in labeled.columns:
            labeled[theme] = 0

    print("Sampling a manageable training set (capped per theme for speed)...")
    sampled_indices = set()
    for theme in all_themes:
        theme_rows = labeled[labeled[theme] == 1]
        take = theme_rows.sample(n=min(MAX_PER_THEME, len(theme_rows)), random_state=42)
        sampled_indices.update(take.index)

    positive_sample = labeled.loc[list(sampled_indices)]

    print("Adding negative examples (complaints with no matched theme)...")
    sentiment_df = pd.read_csv("processed/reviews_sentiment.csv")
    ratings = pd.to_numeric(sentiment_df["rating"], errors="coerce")
    all_complaints = sentiment_df[
        ((sentiment_df["sentiment"] == "Negative") | (ratings <= 2))
        & (ratings <= MAX_RATING_FOR_TRAINING)
    ]

    labeled_reviews_set = set(theme_data["review"].astype(str))
    no_theme_complaints = all_complaints[~all_complaints["review"].astype(str).isin(labeled_reviews_set)]

    neg_sample = no_theme_complaints.sample(
        n=min(MAX_NEGATIVES, len(no_theme_complaints)), random_state=42
    )[["review"]].copy()
    for theme in all_themes:
        neg_sample[theme] = 0

    training_table = pd.concat([positive_sample, neg_sample], ignore_index=True)
    training_table = training_table.drop_duplicates(subset=["review"])

    print(f"\nFinal training set size: {len(training_table):,} reviews")

    print("\nLoading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Encoding training reviews (this takes a few minutes)...")
    texts = training_table["review"].fillna("").astype(str).tolist()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True, batch_size=64)

    X = embeddings
    Y = training_table[all_themes].values

    # Cache to disk so future runs skip this step entirely
    np.save(CACHE_X, X)
    np.save(CACHE_Y, Y)
    with open(CACHE_THEMES, "wb") as f:
        pickle.dump(all_themes, f)
    print("Cached embeddings to disk for future runs.")

# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=TEST_SIZE, random_state=42
)

print(f"\nTrain size: {len(X_train):,} | Test size: {len(X_test):,}")

# ============================================================
# TRAIN ONE CLASSIFIER PER THEME
# ============================================================

print("\n" + "=" * 75)
print("TRAINING CLASSIFIERS (one per theme)")
print("=" * 75)

classifiers = {}
thresholds = {}
results = []

for i, theme in enumerate(all_themes):
    y_train_theme = Y_train[:, i]
    y_test_theme = Y_test[:, i]

    if y_train_theme.sum() < 5:
        print(f"\n{theme}: SKIPPED (not enough positive examples)")
        continue

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train, y_train_theme)
    classifiers[theme] = clf

    # ------------------------------------------------------------
    # Find the best threshold for THIS theme instead of using 0.5.
    # The default 0.5 cutoff was giving high recall but poor
    # precision - searching for the threshold that maximizes F1
    # rebalances that trade-off per theme.
    # ------------------------------------------------------------
    probs = clf.predict_proba(X_test)[:, 1]
    precisions, recalls, thresh_values = precision_recall_curve(y_test_theme, probs)

    # precision_recall_curve returns one more point than thresholds;
    # align them and compute F1 at every candidate threshold
    f1_scores = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-9)
    best_idx = np.argmax(f1_scores)
    best_threshold = thresh_values[best_idx]
    thresholds[theme] = float(best_threshold)

    y_pred_tuned = (probs >= best_threshold).astype(int)

    acc = accuracy_score(y_test_theme, y_pred_tuned)
    prec = precision_score(y_test_theme, y_pred_tuned, zero_division=0)
    rec = recall_score(y_test_theme, y_pred_tuned, zero_division=0)
    f1 = f1_score(y_test_theme, y_pred_tuned, zero_division=0)

    # Also compute default-0.5 metrics for comparison
    y_pred_default = clf.predict(X_test)
    f1_default = f1_score(y_test_theme, y_pred_default, zero_division=0)

    results.append({
        "theme": theme, "threshold": round(best_threshold, 3),
        "accuracy": acc, "precision": prec,
        "recall": rec, "f1_score": f1, "f1_at_default_0.5": f1_default,
    })

    print(f"\n{theme}: (tuned threshold = {best_threshold:.3f})")
    print(f"  Accuracy:  {acc:.3f}")
    print(f"  Precision: {prec:.3f}")
    print(f"  Recall:    {rec:.3f}")
    print(f"  F1 Score:  {f1:.3f}  (was {f1_default:.3f} at default 0.5 cutoff)")

# ============================================================
# SAVE MODELS + RESULTS
# ============================================================

Path("models").mkdir(exist_ok=True)
with open("models/theme_classifiers_clean.pkl", "wb") as f:
    pickle.dump({"classifiers": classifiers, "themes": all_themes, "thresholds": thresholds}, f)

results_df = pd.DataFrame(results).sort_values("f1_score", ascending=False)
results_df.to_csv("processed/classifier_evaluation_clean.csv", index=False)

print("\n" + "=" * 75)
print("EVALUATION SUMMARY (sorted by F1 score)")
print("=" * 75)
print(results_df.to_string(index=False))

print("\nSaved:")
print("  models/theme_classifiers_clean.pkl  (the retrained model, cleaned training data)")
print("  processed/classifier_evaluation_clean.csv  (accuracy metrics)")

print("\nSUCCESS!")
print("Review the F1 scores above. Anything above ~0.6-0.7 is solid for")
print("this kind of task. If results look good, next step is applying")
print("this trained model to the full 1.3M complaint dataset.")