import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

INPUT_FILE = Path("./processed/reviews_sentiment.csv")

CHUNK_SIZE = 50_000


def rating_to_sentiment(rating):
    if pd.isna(rating):
        return None

    rating = float(rating)

    if rating <= 2:
        return "Negative"
    elif rating == 3:
        return "Neutral"
    else:
        return "Positive"


def main():

    print("=" * 70)
    print("LUMINA - SENTIMENT VALIDATION")
    print("=" * 70)

    if not INPUT_FILE.exists():
        print("ERROR: Sentiment dataset not found:")
        print(INPUT_FILE)
        return

    all_true = []
    all_pred = []

    total_rows = 0
    skipped = 0

    print()
    print("Using rating-based weak labels:")
    print("1-2 stars → Negative")
    print("3 stars   → Neutral")
    print("4-5 stars → Positive")
    print()

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE,
            encoding="utf-8",
            low_memory=True
        ),
        start=1
    ):

        total_rows += len(chunk)

        # Create weak ground-truth label
        chunk["rating_label"] = chunk["rating"].apply(
            rating_to_sentiment
        )

        # Remove reviews without valid ratings
        valid = chunk["rating_label"].notna()

        skipped += (~valid).sum()

        chunk = chunk[valid]

        all_true.extend(
            chunk["rating_label"].tolist()
        )

        all_pred.extend(
            chunk["sentiment"].tolist()
        )

        print(
            f"Chunk {chunk_number:>4} | "
            f"Processed: {total_rows:>10,}"
        )

    print()
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    accuracy = accuracy_score(
        all_true,
        all_pred
    )

    precision = precision_score(
        all_true,
        all_pred,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        all_true,
        all_pred,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        all_true,
        all_pred,
        average="weighted",
        zero_division=0
    )

    print()
    print(f"Reviews evaluated : {len(all_true):,}")
    print(f"Reviews skipped   : {skipped:,}")
    print()
    print(f"Accuracy          : {accuracy:.4f}")
    print(f"Precision         : {precision:.4f}")
    print(f"Recall            : {recall:.4f}")
    print(f"F1 Score          : {f1:.4f}")

    # ========================================================
    # CLASSIFICATION REPORT
    # ========================================================

    print()
    print("=" * 70)
    print("CLASSIFICATION REPORT")
    print("=" * 70)

    print(
        classification_report(
            all_true,
            all_pred,
            labels=[
                "Negative",
                "Neutral",
                "Positive"
            ],
            zero_division=0
        )
    )

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    cm = confusion_matrix(
        all_true,
        all_pred,
        labels=[
            "Negative",
            "Neutral",
            "Positive"
        ]
    )

    print("=" * 70)
    print("CONFUSION MATRIX")
    print("=" * 70)

    print()
    print("                 Predicted")
    print("              Neg    Neu    Pos")
    print(
        f"Actual Neg   {cm[0][0]:6,} "
        f"{cm[0][1]:6,} "
        f"{cm[0][2]:6,}"
    )

    print(
        f"Actual Neu   {cm[1][0]:6,} "
        f"{cm[1][1]:6,} "
        f"{cm[1][2]:6,}"
    )

    print(
        f"Actual Pos   {cm[2][0]:6,} "
        f"{cm[2][1]:6,} "
        f"{cm[2][2]:6,}"
    )

    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)

    print()
    print("IMPORTANT:")
    print(
        "These results use star ratings as WEAK labels, "
        "not human-verified ground truth."
    )


if __name__ == "__main__":
    main()