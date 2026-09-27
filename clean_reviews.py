import pandas as pd
from pathlib import Path
import re
import time

# ============================================================
# LUMINA - REVIEW CLEANING PIPELINE
# ============================================================

INPUT_FILE = Path("./processed/all_unique_reviews.csv")
OUTPUT_DIR = Path("./processed")
OUTPUT_FILE = OUTPUT_DIR / "reviews_clean.csv"

CHUNK_SIZE = 50_000


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # Remove null/control characters
    text = text.replace("\x00", " ")
    text = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# PII REDACTION
# ============================================================

def redact_pii(text):
    if not text:
        return text

    # Email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL]",
        text
    )

    # URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        "[URL]",
        text,
        flags=re.IGNORECASE
    )

    # Phone numbers
    text = re.sub(
        r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)",
        "[PHONE]",
        text
    )

    # Order numbers / long numeric IDs
    text = re.sub(
        r"\b(?:order|order\s*id|tracking|tracking\s*id)"
        r"\s*[:#-]?\s*[A-Z0-9-]{6,}\b",
        "[ORDER_ID]",
        text,
        flags=re.IGNORECASE
    )

    return text


# ============================================================
# QUALITY FILTER
# ============================================================

def is_valid_review(text):
    if not text:
        return False

    # Too short to provide useful feedback
    if len(text) < 3:
        return False

    # Remove reviews consisting almost entirely of symbols
    alphanumeric_count = sum(c.isalnum() for c in text)

    if alphanumeric_count < 3:
        return False

    return True


# ============================================================
# MAIN PROCESSING
# ============================================================

def main():

    print("=" * 70)
    print("LUMINA - ENTERPRISE REVIEW CLEANING")
    print("=" * 70)

    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found:")
        print(INPUT_FILE)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Delete previous output
    if OUTPUT_FILE.exists():
        print("Existing cleaned dataset found.")
        print("Deleting old version...")
        OUTPUT_FILE.unlink()

    total_rows = 0
    valid_rows = 0
    removed_rows = 0
    pii_redactions = 0
    chunks = 0

    start_time = time.time()
    first_write = True

    print()
    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Chunk size: {CHUNK_SIZE:,}")
    print()
    print("Starting processing...")
    print()

    try:

        for chunk in pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE,
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="skip",
            low_memory=True
        ):

            chunks += 1
            total_rows += len(chunk)

            # ------------------------------------------------
            # Clean review text
            # ------------------------------------------------

            chunk["review"] = chunk["review"].apply(clean_text)

            # ------------------------------------------------
            # Quality filtering
            # ------------------------------------------------

            valid_mask = chunk["review"].apply(is_valid_review)

            removed_rows += (~valid_mask).sum()

            chunk = chunk[valid_mask].copy()

            if len(chunk) == 0:
                continue

            # ------------------------------------------------
            # PII detection/redaction
            # ------------------------------------------------

            before_pii = chunk["review"].copy()

            chunk["review"] = chunk["review"].apply(redact_pii)

            pii_changed = (
                before_pii != chunk["review"]
            ).sum()

            pii_redactions += pii_changed

            # ------------------------------------------------
            # Normalize rating
            # ------------------------------------------------

            chunk["rating"] = pd.to_numeric(
                chunk["rating"],
                errors="coerce"
            )

            # Keep ratings in valid range
            chunk.loc[
                ~chunk["rating"].between(1, 5),
                "rating"
            ] = pd.NA

            # ------------------------------------------------
            # Add useful metadata
            # ------------------------------------------------

            chunk["review_length"] = (
                chunk["review"].str.len()
            )

            chunk["word_count"] = (
                chunk["review"]
                .str.split()
                .str.len()
            )

            # ------------------------------------------------
            # Remove duplicates — but ONLY when the same
            # reviewerID posted the exact same review text more
            # than once (e.g. an accidental double-submit, or a
            # cross-posted review). Two different customers who
            # happen to write similar or identical short text
            # ("Great product!") are two different people and are
            # always both kept, regardless of category.
            # ------------------------------------------------

            before_duplicates = len(chunk)

            if "reviewerID" in chunk.columns:
                has_id = chunk["reviewerID"].notna() & (chunk["reviewerID"].astype(str).str.strip() != "")
                with_id = chunk[has_id].drop_duplicates(subset=["reviewerID", "review"])
                without_id = chunk[~has_id]  # can't confirm authorship, so never deduped
                chunk = pd.concat([with_id, without_id], ignore_index=True)
            else:
                # No reviewerID column at all in this input — can't do
                # id-based dedup, so skip dedup here rather than fall
                # back to the old text-only behavior (which wrongly
                # drops different people's similar reviews).
                pass

            removed_rows += (
                before_duplicates - len(chunk)
            )

            valid_rows += len(chunk)

            # ------------------------------------------------
            # Save
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
                f"Chunk {chunks:>4} | "
                f"Processed: {total_rows:>10,} | "
                f"Saved: {valid_rows:>10,} | "
                f"Removed: {removed_rows:>8,} | "
                f"Time: {elapsed / 60:.2f} min"
            )

    except Exception as e:

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print(e)
        return

    # ========================================================
    # FINAL REPORT
    # ========================================================

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)

    print(f"Rows processed:       {total_rows:,}")
    print(f"Clean reviews saved:  {valid_rows:,}")
    print(f"Rows removed:         {removed_rows:,}")
    print(f"PII-containing rows:  {pii_redactions:,}")
    print(f"Processing time:      {elapsed / 60:.2f} minutes")
    print()
    print(f"Output:")
    print(OUTPUT_FILE)

    # ========================================================
    # VERIFY OUTPUT
    # ========================================================

    if OUTPUT_FILE.exists():

        print()
        print("=" * 70)
        print("VERIFYING CLEAN DATASET")
        print("=" * 70)

        category_counts = {}
        total_output = 0

        for chunk in pd.read_csv(
            OUTPUT_FILE,
            chunksize=50_000
        ):

            total_output += len(chunk)

            counts = chunk["category"].value_counts()

            for category, count in counts.items():

                category_counts[category] = (
                    category_counts.get(category, 0)
                    + int(count)
                )

        print(f"Verified rows: {total_output:,}")
        print()
        print("Reviews by category:")

        for category, count in sorted(
            category_counts.items()
        ):
            print(f"  {category}: {count:,}")

        print()
        print("Columns:")

        sample = pd.read_csv(
            OUTPUT_FILE,
            nrows=5
        )

        print(list(sample.columns))

        print()
        print("SUCCESS!")
        print("Clean enterprise-ready dataset created.")


if __name__ == "__main__":
    main()