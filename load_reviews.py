import pandas as pd
from pathlib import Path
import hashlib
import re
import sys
import time


# ============================================================
# LUMINA - FULL REVIEW DATA LOADER
# ============================================================
# Purpose:
#   1. Read all five raw CSV files
#   2. Process large files in chunks
#   3. Find review text and rating columns automatically
#   4. Remove empty/invalid reviews
#   5. Remove duplicate reviews
#   6. Keep ALL available unique reviews
#   7. Save the result into processed/
#
# The script does NOT load the entire multi-GB dataset into RAM.
# ============================================================


# -----------------------------
# SETTINGS
# -----------------------------

RAW_DATA_DIR = Path("./raw_data")
PROCESSED_DIR = Path("./processed")

OUTPUT_FILE = PROCESSED_DIR / "all_unique_reviews.csv"

# Number of rows processed at a time.
# 5,000 is safer for a laptop.
CHUNK_SIZE = 5000


# Your five source files
FILES = [
    ("Arts & Crafts & Sewing", "arts_crafts_sewing.csv"),
    ("Digital Music", "digital_music.csv"),
    ("Electronics", "electronics_1.csv"),
    ("Electronics", "electronics_2.csv"),
    ("Fashion", "fashion.csv"),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_review_text(text):
    """
    Basic cleaning of review text.

    We are NOT doing aggressive NLP cleaning here.
    We want to preserve the original meaning for later
    sentiment and theme analysis.
    """

    if pd.isna(text):
        return ""

    text = str(text)

    # Remove null characters
    text = text.replace("\x00", " ")

    # Replace excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_for_duplicate(text):
    """
    Creates a normalized version of a review for duplicate detection.

    Example:

    "THIS PRODUCT IS GREAT!!!"
    "this product is great"

    will be treated as the same review.

    The original review text is NOT changed.
    """

    text = text.lower()

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    return text.strip()


def review_hash(text):
    """
    Creates a compact hash for efficient duplicate detection.
    """

    normalized = normalize_for_duplicate(text)

    return hashlib.sha256(
        normalized.encode("utf-8", errors="ignore")
    ).hexdigest()


def find_review_column(columns):
    """
    Automatically finds the review-text column.
    """

    possible_names = [
        "reviewText",
        "review_text",
        "review",
        "Review Text",
        "ReviewText",
        "text",
        "Text",
        "content",
        "Content",
    ]

    # Exact matching first
    for name in possible_names:
        if name in columns:
            return name

    # Case-insensitive matching
    lower_columns = {
        str(col).lower(): col
        for col in columns
    }

    for name in possible_names:
        if name.lower() in lower_columns:
            return lower_columns[name.lower()]

    return None


def find_rating_column(columns):
    """
    Automatically finds the rating column.
    """

    possible_names = [
        "overall",
        "rating",
        "Rating",
        "stars",
        "Stars",
        "score",
        "Score",
    ]

    for name in possible_names:
        if name in columns:
            return name

    lower_columns = {
        str(col).lower(): col
        for col in columns
    }

    for name in possible_names:
        if name.lower() in lower_columns:
            return lower_columns[name.lower()]

    return None


# ============================================================
# PROCESS ONE CSV FILE
# ============================================================

def process_file(category, filename, seen_hashes, output_file):
    """
    Process one CSV file chunk-by-chunk.

    Returns statistics.
    """

    path = RAW_DATA_DIR / filename

    if not path.exists():

        print()
        print("=" * 60)
        print("WARNING")
        print("=" * 60)
        print(f"File not found: {path}")
        print("Skipping this file.")
        return {
            "rows": 0,
            "valid": 0,
            "duplicates": 0,
            "written": 0,
        }

    print()
    print("=" * 60)
    print(f"PROCESSING: {category}")
    print(f"FILE: {filename}")
    print("=" * 60)

    total_rows = 0
    valid_reviews = 0
    duplicate_reviews = 0
    written_reviews = 0

    review_column = None
    rating_column = None

    first_output = not output_file.exists()

    start_time = time.time()

    try:

        # ----------------------------------------------------
        # Read CSV in chunks
        # ----------------------------------------------------

        for chunk_number, chunk in enumerate(
            pd.read_csv(
                path,
                chunksize=CHUNK_SIZE,
                encoding="utf-8",
                encoding_errors="replace",
                on_bad_lines="skip",
                low_memory=True
            ),
            start=1
        ):

            total_rows += len(chunk)

            # ------------------------------------------------
            # Identify columns from first chunk
            # ------------------------------------------------

            if review_column is None:

                review_column = find_review_column(
                    chunk.columns
                )

                rating_column = find_rating_column(
                    chunk.columns
                )

                print()
                print("Columns detected:")
                print(list(chunk.columns))

                print()
                print(f"Review column: {review_column}")
                print(f"Rating column: {rating_column}")

                if review_column is None:

                    print()
                    print("ERROR:")
                    print(
                        "Could not find the review text column."
                    )

                    print()
                    print(
                        "Available columns:"
                    )

                    print(list(chunk.columns))

                    return {
                        "rows": total_rows,
                        "valid": 0,
                        "duplicates": 0,
                        "written": 0,
                    }

            # ------------------------------------------------
            # Extract review text
            # ------------------------------------------------

            reviews = chunk[review_column].apply(
                clean_review_text
            )

            # Remove empty reviews
            valid_mask = (
                reviews.str.len() > 0
            )

            reviews = reviews[valid_mask]

            if len(reviews) == 0:
                continue

            valid_reviews += len(reviews)

            # ------------------------------------------------
            # Build output dataframe
            # ------------------------------------------------

            output = pd.DataFrame()

            output["review"] = reviews.values

            # Rating
            if rating_column is not None:

                ratings = pd.to_numeric(
                    chunk.loc[
                        valid_mask,
                        rating_column
                    ],
                    errors="coerce"
                )

                output["rating"] = ratings.values

            else:

                output["rating"] = pd.NA

            # Category
            output["category"] = category

            # ------------------------------------------------
            # Generate duplicate hashes
            # ------------------------------------------------

            output["_hash"] = output["review"].apply(
                review_hash
            )

            # ------------------------------------------------
            # Remove duplicates within current chunk
            # ------------------------------------------------

            before_chunk = len(output)

            output = output.drop_duplicates(
                subset=["_hash"]
            )

            duplicate_reviews += (
                before_chunk - len(output)
            )

            # ------------------------------------------------
            # Remove duplicates already seen in previous chunks
            # ------------------------------------------------

            unique_rows = []

            for _, row in output.iterrows():

                current_hash = row["_hash"]

                if current_hash in seen_hashes:

                    duplicate_reviews += 1

                else:

                    seen_hashes.add(current_hash)

                    unique_rows.append(row)

            if not unique_rows:
                continue

            output = pd.DataFrame(
                unique_rows
            )

            # ------------------------------------------------
            # Remove internal hash
            # ------------------------------------------------

            output = output[
                [
                    "review",
                    "rating",
                    "category"
                ]
            ]

            # ------------------------------------------------
            # Write to output CSV
            # ------------------------------------------------

            output.to_csv(
                output_file,
                mode="w" if first_output else "a",
                header=first_output,
                index=False,
                encoding="utf-8"
            )

            first_output = False

            written_reviews += len(output)

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            elapsed = time.time() - start_time

            print(
                f"Chunk {chunk_number:,} | "
                f"Rows: {total_rows:,} | "
                f"Unique written: {written_reviews:,} | "
                f"Duplicates: {duplicate_reviews:,} | "
                f"Time: {elapsed:.1f}s"
            )

    except Exception as e:

        print()
        print("=" * 60)
        print("ERROR WHILE PROCESSING FILE")
        print("=" * 60)

        print(f"File: {filename}")
        print(f"Error: {e}")

        print()

        return {
            "rows": total_rows,
            "valid": valid_reviews,
            "duplicates": duplicate_reviews,
            "written": written_reviews,
        }

    elapsed = time.time() - start_time

    print()
    print(f"Finished: {filename}")
    print(f"Rows scanned: {total_rows:,}")
    print(f"Valid reviews: {valid_reviews:,}")
    print(f"Duplicates removed: {duplicate_reviews:,}")
    print(f"Unique reviews written: {written_reviews:,}")
    print(f"Time: {elapsed:.1f} seconds")

    return {
        "rows": total_rows,
        "valid": valid_reviews,
        "duplicates": duplicate_reviews,
        "written": written_reviews,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("LUMINA - FULL REVIEW DATA LOADER")
    print("=" * 60)

    print()
    print("Mode: ALL UNIQUE REVIEWS")
    print(f"Chunk size: {CHUNK_SIZE:,}")
    print(f"Output: {OUTPUT_FILE}")

    # --------------------------------------------------------
    # Check raw data folder
    # --------------------------------------------------------

    if not RAW_DATA_DIR.exists():

        print()
        print("ERROR:")
        print(
            f"Raw data folder does not exist: "
            f"{RAW_DATA_DIR}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Create processed folder
    # --------------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Remove old output
    # --------------------------------------------------------

    if OUTPUT_FILE.exists():

        print()
        print("Existing output detected:")
        print(OUTPUT_FILE)

        print()
        print("Deleting old output...")

        OUTPUT_FILE.unlink()

    # --------------------------------------------------------
    # Global duplicate set
    # --------------------------------------------------------

    seen_hashes = set()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_rows = 0
    total_valid = 0
    total_duplicates = 0
    total_written = 0

    overall_start = time.time()

    # --------------------------------------------------------
    # Process all files
    # --------------------------------------------------------

    for category, filename in FILES:

        stats = process_file(
            category,
            filename,
            seen_hashes,
            OUTPUT_FILE
        )

        total_rows += stats["rows"]
        total_valid += stats["valid"]
        total_duplicates += stats["duplicates"]
        total_written += stats["written"]

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    overall_time = time.time() - overall_start

    print()
    print()
    print("=" * 60)
    print("LUMINA DATA LOADING COMPLETE")
    print("=" * 60)

    print()
    print(f"Total rows scanned:       {total_rows:,}")
    print(f"Valid reviews:            {total_valid:,}")
    print(f"Duplicate reviews:        {total_duplicates:,}")
    print(f"Unique reviews saved:     {total_written:,}")

    print()
    print(f"Output file:")
    print(OUTPUT_FILE)

    print()
    print(
        f"Total processing time: "
        f"{overall_time / 60:.2f} minutes"
    )

    # --------------------------------------------------------
    # Verify output
    # --------------------------------------------------------

    if OUTPUT_FILE.exists():

        print()
        print("=" * 60)
        print("VERIFYING OUTPUT")
        print("=" * 60)

        try:

            # Read only columns/statistics in chunks
            category_counts = {}
            output_rows = 0

            for chunk in pd.read_csv(
                OUTPUT_FILE,
                chunksize=10000
            ):

                output_rows += len(chunk)

                counts = chunk[
                    "category"
                ].value_counts()

                for category, count in counts.items():

                    category_counts[category] = (
                        category_counts.get(
                            category,
                            0
                        ) + int(count)
                    )

            print()
            print(
                f"Verified rows: {output_rows:,}"
            )

            print()
            print("Reviews by category:")

            for category, count in sorted(
                category_counts.items()
            ):

                print(
                    f"  {category}: {count:,}"
                )

            print()
            print("SUCCESS!")
            print(
                "Your complete unique review dataset "
                "has been created."
            )

        except Exception as e:

            print()
            print(
                f"Could not verify output: {e}"
            )

    else:

        print()
        print("WARNING:")
        print(
            "No output file was created."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()