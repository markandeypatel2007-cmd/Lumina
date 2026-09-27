import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re
import time

# ============================================================
# LUMINA - CUSTOMER COMPLAINT / THEME ANALYSIS
# ============================================================

INPUT_FILE = Path("./processed/reviews_sentiment.csv")
OUTPUT_DIR = Path("./processed")

THEME_FILE = OUTPUT_DIR / "top_complaint_terms.csv"
VERBATIM_FILE = OUTPUT_DIR / "complaint_verbatims.csv"

CHUNK_SIZE = 50_000

# Number of negative reviews to analyze
MAX_NEGATIVE_REVIEWS = 300_000


# ============================================================
# TEXT PREPROCESSING
# ============================================================

def clean_for_analysis(text):

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LUMINA - CUSTOMER COMPLAINT ANALYSIS")
    print("=" * 70)

    if not INPUT_FILE.exists():
        print("ERROR: Sentiment dataset not found:")
        print(INPUT_FILE)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    negative_reviews = []

    total_processed = 0
    total_negative = 0

    print()
    print("Reading negative reviews...")
    print(f"Maximum reviews for analysis: {MAX_NEGATIVE_REVIEWS:,}")
    print()

    # ========================================================
    # READ DATA IN CHUNKS
    # ========================================================

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE,
            encoding="utf-8",
            low_memory=True
        ),
        start=1
    ):

        total_processed += len(chunk)

        # Select negative reviews
        negative = chunk[
            chunk["sentiment"] == "Negative"
        ].copy()

        total_negative += len(negative)

        if len(negative) > 0:

            negative_reviews.extend(
                negative[
                    [
                        "review",
                        "rating",
                        "category",
                        "sentiment_score",
                        "sentiment_confidence"
                    ]
                ].to_dict("records")
            )

        print(
            f"Chunk {chunk_number:>4} | "
            f"Processed: {total_processed:>10,} | "
            f"Negative found: {total_negative:>10,}"
        )

        if len(negative_reviews) >= MAX_NEGATIVE_REVIEWS:
            print()
            print("Maximum negative-review sample reached.")
            break

    print()
    print("=" * 70)
    print("NEGATIVE REVIEW COLLECTION COMPLETE")
    print("=" * 70)

    # Limit exact number
    negative_reviews = negative_reviews[
        :MAX_NEGATIVE_REVIEWS
    ]

    print(
        f"Negative reviews analyzed: "
        f"{len(negative_reviews):,}"
    )

    # ========================================================
    # CREATE DATAFRAME
    # ========================================================

    df = pd.DataFrame(negative_reviews)

    if df.empty:

        print("No negative reviews found.")
        return

    df["analysis_text"] = (
        df["review"]
        .apply(clean_for_analysis)
    )

    # ========================================================
    # TF-IDF
    # ========================================================

    print()
    print("=" * 70)
    print("EXTRACTING COMPLAINT TERMS")
    print("=" * 70)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=20,
        max_df=0.85,
        max_features=10_000,
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        df["analysis_text"]
    )

    terms = vectorizer.get_feature_names_out()

    # Average TF-IDF score for each term
    scores = matrix.mean(axis=0).A1

    term_scores = pd.DataFrame({
        "term": terms,
        "tfidf_score": scores
    })

    term_scores = term_scores.sort_values(
        "tfidf_score",
        ascending=False
    )

    # Save top terms
    term_scores.head(500).to_csv(
        THEME_FILE,
        index=False
    )

    print()
    print("Top complaint-related terms:")
    print()

    print(
        term_scores
        .head(50)
        .to_string(index=False)
    )

    # ========================================================
    # EXTRACT REPRESENTATIVE VERBATIMS
    # ========================================================

    print()
    print("=" * 70)
    print("EXTRACTING CUSTOMER VERBATIMS")
    print("=" * 70)

    # Use top terms to locate real reviews
    top_terms = term_scores.head(30)["term"].tolist()

    verbatims = []

    for term in top_terms:

        # Escape regex characters
        pattern = re.escape(term)

        matches = df[
            df["analysis_text"].str.contains(
                pattern,
                regex=True,
                na=False
            )
        ]

        # Take up to 5 examples per term
        examples = matches.head(5)

        for _, row in examples.iterrows():

            verbatims.append({
                "theme_term": term,
                "category": row["category"],
                "rating": row["rating"],
                "sentiment_score": row["sentiment_score"],
                "review": row["review"]
            })

    verbatim_df = pd.DataFrame(verbatims)

    verbatim_df.to_csv(
        VERBATIM_FILE,
        index=False,
        encoding="utf-8"
    )

    print()
    print(
        f"Verbatims saved: "
        f"{len(verbatim_df):,}"
    )

    # ========================================================
    # CATEGORY BREAKDOWN
    # ========================================================

    print()
    print("=" * 70)
    print("NEGATIVE REVIEWS BY CATEGORY")
    print("=" * 70)

    category_counts = (
        df["category"]
        .value_counts()
    )

    print(category_counts)

    # ========================================================
    # FINAL
    # ========================================================

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("THEME ANALYSIS COMPLETE")
    print("=" * 70)

    print(f"Reviews analyzed: {len(df):,}")
    print(f"Unique terms:     {len(term_scores):,}")
    print(f"Processing time:  {elapsed / 60:.2f} minutes")

    print()
    print("Output files:")

    print(THEME_FILE)
    print(VERBATIM_FILE)

    print()
    print("SUCCESS!")


if __name__ == "__main__":
    main()