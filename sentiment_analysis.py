import pandas as pd
from pathlib import Path
from nltk.sentiment import SentimentIntensityAnalyzer
import time

# ============================================================
# LUMINA - SENTIMENT ANALYSIS
# ============================================================

INPUT_FILE = Path("./processed/reviews_clean.csv")
OUTPUT_FILE = Path("./processed/reviews_sentiment.csv")

CHUNK_SIZE = 50_000


def classify_sentiment(score):
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"


def calculate_confidence(scores):
    """
    Convert distance from neutral into a simple confidence score.

    0.0  = very close to neutral
    1.0  = very strongly positive/negative
    """
    return min(abs(scores) * 1.5, 1.0)


def main():

    print("=" * 70)
    print("LUMINA - SENTIMENT ANALYSIS ENGINE")
    print("=" * 70)

    if not INPUT_FILE.exists():
        print("ERROR: Clean dataset not found:")
        print(INPUT_FILE)
        return

    # Delete previous output
    if OUTPUT_FILE.exists():
        print("Existing sentiment dataset found.")
        print("Deleting old version...")
        OUTPUT_FILE.unlink()

    analyzer = SentimentIntensityAnalyzer()

    total_processed = 0
    positive = 0
    negative = 0
    neutral = 0
    first_write = True

    start_time = time.time()

    print()
    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Chunk size: {CHUNK_SIZE:,}")
    print()
    print("Starting sentiment analysis...")
    print()

    try:

        for chunk_number, chunk in enumerate(
            pd.read_csv(
                INPUT_FILE,
                chunksize=CHUNK_SIZE,
                encoding="utf-8",
                encoding_errors="replace",
                low_memory=True
            ),
            start=1
        ):

            # ------------------------------------------------
            # Run VADER
            # ------------------------------------------------

            scores = chunk["review"].apply(
                analyzer.polarity_scores
            )

            # Extract compound score
            chunk["sentiment_score"] = scores.apply(
                lambda x: x["compound"]
            )

            # Sentiment label
            chunk["sentiment"] = chunk["sentiment_score"].apply(
                classify_sentiment
            )

            # Confidence
            chunk["sentiment_confidence"] = (
                chunk["sentiment_score"]
                .apply(calculate_confidence)
            )

            # ------------------------------------------------
            # Count sentiments
            # ------------------------------------------------

            positive += (
                chunk["sentiment"] == "Positive"
            ).sum()

            negative += (
                chunk["sentiment"] == "Negative"
            ).sum()

            neutral += (
                chunk["sentiment"] == "Neutral"
            ).sum()

            total_processed += len(chunk)

            # ------------------------------------------------
            # Save chunk
            # ------------------------------------------------

            chunk.to_csv(
                OUTPUT_FILE,
                mode="w" if first_write else "a",
                header=first_write,
                index=False,
                encoding="utf-8"
            )

            first_write = False

            elapsed = time.time() - start_time

            print(
                f"Chunk {chunk_number:>4} | "
                f"Processed: {total_processed:>10,} | "
                f"Positive: {positive:>10,} | "
                f"Negative: {negative:>10,} | "
                f"Neutral: {neutral:>10,} | "
                f"Time: {elapsed / 60:.2f} min"
            )

    except Exception as e:

        print()
        print("=" * 70)
        print("ERROR DURING SENTIMENT ANALYSIS")
        print("=" * 70)
        print(e)
        return

    # ========================================================
    # FINAL REPORT
    # ========================================================

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("SENTIMENT ANALYSIS COMPLETE")
    print("=" * 70)

    print(f"Total reviews processed: {total_processed:,}")
    print(f"Positive:                {positive:,}")
    print(f"Negative:                {negative:,}")
    print(f"Neutral:                 {neutral:,}")
    print(f"Processing time:         {elapsed / 60:.2f} minutes")

    if total_processed > 0:

        print()
        print("Sentiment distribution:")

        print(
            f"Positive: "
            f"{positive / total_processed * 100:.2f}%"
        )

        print(
            f"Negative: "
            f"{negative / total_processed * 100:.2f}%"
        )

        print(
            f"Neutral: "
            f"{neutral / total_processed * 100:.2f}%"
        )

    print()
    print(f"Output file:")
    print(OUTPUT_FILE)

    # ========================================================
    # VERIFY
    # ========================================================

    print()
    print("=" * 70)
    print("VERIFYING OUTPUT")
    print("=" * 70)

    if OUTPUT_FILE.exists():

        sample = pd.read_csv(
            OUTPUT_FILE,
            nrows=5
        )

        print()
        print("Columns:")
        print(list(sample.columns))

        print()
        print("Sample results:")

        print(
            sample[
                [
                    "review",
                    "rating",
                    "category",
                    "sentiment",
                    "sentiment_score",
                    "sentiment_confidence"
                ]
            ].to_string(index=False)
        )

        print()
        print("SUCCESS!")
        print("Sentiment dataset created successfully.")


if __name__ == "__main__":
    main()