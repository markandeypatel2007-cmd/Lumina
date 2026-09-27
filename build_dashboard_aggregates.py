"""
Precompute small dashboard files from the 6.8M sentiment CSV.

Does NOT reload theme matching on the full set. Overall KPIs come from
every row; aspect/phrase/word-cloud views come from a systematic sample
so the app stays interactive.

Run:
    python build_dashboard_aggregates.py
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

from analyze_reviews import analyze_frame

INPUT = Path("processed/reviews_sentiment.csv")
OUT = Path("processed")
CHUNK = 50_000
SAMPLE_EVERY = 270  # ~6.8M / 270 ≈ 25k rows
SAMPLE_CAP = 25_000
MISMATCH_CAP = 400

USECOLS = [
    "review", "rating", "category", "reviewTime", "unixReviewTime",
    "sentiment", "sentiment_score",
]


def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}")

    sent_counts = defaultdict(int)
    cat_counts = defaultdict(lambda: defaultdict(int))
    cat_rating_sum = defaultdict(float)
    cat_rating_n = defaultdict(int)
    rating_sent = defaultdict(lambda: defaultdict(int))
    month_sent = defaultdict(lambda: defaultdict(int))
    total = 0
    rating_sum = 0.0
    rating_n = 0
    sample_rows = []
    mismatch_high = []
    mismatch_low = []

    print("Scanning reviews_sentiment.csv ...")
    for i, chunk in enumerate(
        pd.read_csv(
            INPUT,
            usecols=lambda c: c in USECOLS,
            chunksize=CHUNK,
            encoding="utf-8",
            encoding_errors="replace",
            low_memory=True,
        ),
        start=1,
    ):
        total += len(chunk)
        vc = chunk["sentiment"].value_counts()
        for k, v in vc.items():
            sent_counts[str(k)] += int(v)

        ratings = pd.to_numeric(chunk["rating"], errors="coerce")
        rating_sum += float(ratings.sum(skipna=True))
        rating_n += int(ratings.notna().sum())

        for (cat, sent), n in chunk.groupby(["category", "sentiment"]).size().items():
            cat_counts[str(cat)][str(sent)] += int(n)

        for cat, sub in chunk.groupby("category"):
            r = pd.to_numeric(sub["rating"], errors="coerce")
            cat_rating_sum[str(cat)] += float(r.sum(skipna=True))
            cat_rating_n[str(cat)] += int(r.notna().sum())

        star = ratings.round()
        tmp = pd.DataFrame({"star": star, "sentiment": chunk["sentiment"]})
        tmp = tmp.dropna(subset=["star"])
        for (s, sent), n in tmp.groupby(["star", "sentiment"]).size().items():
            rating_sent[int(s)][str(sent)] += int(n)

        if "unixReviewTime" in chunk.columns:
            months = pd.to_datetime(chunk["unixReviewTime"], unit="s", errors="coerce").dt.to_period("M").astype(str)
            mtmp = pd.DataFrame({"month": months, "sentiment": chunk["sentiment"]})
            mtmp = mtmp[mtmp["month"] != "NaT"]
            for (m, sent), n in mtmp.groupby(["month", "sentiment"]).size().items():
                month_sent[str(m)][str(sent)] += int(n)

        hi = chunk[(ratings >= 5) & (chunk["sentiment"] == "Negative")]
        lo = chunk[(ratings <= 1) & (chunk["sentiment"] == "Positive")]
        if len(mismatch_high) < MISMATCH_CAP and len(hi):
            mismatch_high.extend(hi.head(MISMATCH_CAP - len(mismatch_high)).to_dict("records"))
        if len(mismatch_low) < MISMATCH_CAP and len(lo):
            mismatch_low.extend(lo.head(MISMATCH_CAP - len(mismatch_low)).to_dict("records"))

        if len(sample_rows) < SAMPLE_CAP:
            take = chunk.iloc[::SAMPLE_EVERY]
            sample_rows.extend(take.to_dict("records"))
            sample_rows = sample_rows[:SAMPLE_CAP]

        if i % 20 == 0:
            print(f"  chunk {i:>4} | rows {total:,}")

    pos = sent_counts.get("Positive", 0)
    neg = sent_counts.get("Negative", 0)
    neu = sent_counts.get("Neutral", 0)
    kpis = pd.DataFrame([{
        "total_reviews": total,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "positive_pct": round(100 * pos / total, 2),
        "negative_pct": round(100 * neg / total, 2),
        "neutral_pct": round(100 * neu / total, 2),
        "avg_rating": round(rating_sum / rating_n, 3) if rating_n else None,
        "sample_size": len(sample_rows),
    }])
    kpis.to_csv(OUT / "sentiment_kpis.csv", index=False)

    cat_rows = []
    for cat, sc in cat_counts.items():
        n = sum(sc.values())
        cat_rows.append({
            "product": cat,
            "reviews": n,
            "positive_pct": round(100 * sc.get("Positive", 0) / n, 1),
            "negative_pct": round(100 * sc.get("Negative", 0) / n, 1),
            "neutral_pct": round(100 * sc.get("Neutral", 0) / n, 1),
            "avg_rating": round(cat_rating_sum[cat] / cat_rating_n[cat], 2) if cat_rating_n[cat] else None,
        })
    pd.DataFrame(cat_rows).to_csv(OUT / "category_sentiment.csv", index=False)

    ct_rows = []
    for star, sc in sorted(rating_sent.items()):
        n = sum(sc.values())
        ct_rows.append({
            "stars": star,
            "reviews": n,
            "positive_pct": round(100 * sc.get("Positive", 0) / n, 1),
            "negative_pct": round(100 * sc.get("Negative", 0) / n, 1),
            "neutral_pct": round(100 * sc.get("Neutral", 0) / n, 1),
            "Positive": sc.get("Positive", 0),
            "Negative": sc.get("Negative", 0),
            "Neutral": sc.get("Neutral", 0),
        })
    pd.DataFrame(ct_rows).to_csv(OUT / "rating_sentiment_crosstab.csv", index=False)

    m_rows = []
    for month in sorted(month_sent):
        sc = month_sent[month]
        n = sum(sc.values())
        m_rows.append({
            "month": month,
            "reviews": n,
            "positive_pct": round(100 * sc.get("Positive", 0) / n, 2),
            "negative_pct": round(100 * sc.get("Negative", 0) / n, 2),
            "neutral_pct": round(100 * sc.get("Neutral", 0) / n, 2),
        })
    pd.DataFrame(m_rows).to_csv(OUT / "monthly_sentiment_full.csv", index=False)

    sample = pd.DataFrame(sample_rows)
    sample.to_csv(OUT / "dashboard_sample.csv", index=False)
    print(f"Analyzing sample of {len(sample):,} reviews for aspects / phrases ...")
    metrics = analyze_frame(sample)
    metrics["aspect"].to_csv(OUT / "aspect_sentiment_sample.csv", index=False)
    metrics["complaints"].to_csv(OUT / "complaint_phrases_sample.csv", index=False)
    metrics["likes"].to_csv(OUT / "praise_phrases_sample.csv", index=False)
    metrics["word_cloud"].to_csv(OUT / "complaint_wordcloud_sample.csv", index=False)
    metrics["product_stats"].to_csv(OUT / "category_aspect_sample.csv", index=False)
    pd.DataFrame(mismatch_high).to_csv(OUT / "mismatches_5star_negative.csv", index=False)
    pd.DataFrame(mismatch_low).to_csv(OUT / "mismatches_1star_positive.csv", index=False)

    print("Wrote processed/sentiment_kpis.csv and related dashboard files.")
    print(kpis.to_string(index=False))


if __name__ == "__main__":
    main()
