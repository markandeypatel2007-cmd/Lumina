"""
lumina_api.py
--------------
Lightweight JSON API that connects the new HTML/CSS/JS dashboard to
Lumina's real Python analysis pipeline (url_analyzer.py, product_profile.py,
analyze_reviews.py). No Streamlit involved - this is a standalone Flask app.

First-time setup:
    pip install flask

Run:
    python lumina_api.py

Then open:
    http://localhost:5000

Endpoints:
    GET  /api/global          -> dataset-wide stats. Reads processed/*.csv
                                  produced by build_dashboard_aggregates.py
                                  if present, otherwise returns a 404 with
                                  a clear message telling you to run it.
    POST /api/analyze-url      {url: "..."} -> product-level stats for that
                                  link, via extract_reviews_from_url().
    POST /api/analyze-csv      multipart file upload -> product-level stats
                                  for an uploaded reviews CSV.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from url_analyzer import extract_reviews_from_url
from product_profile import extract_product_profile
from analyze_reviews import analyze_frame, normalize_upload

app = Flask(__name__, static_folder=None)
DASHBOARD_FILE = Path(__file__).parent / "lumina_dashboard.html"
PROCESSED = Path("processed")


def clean(v):
    """Make a value JSON-safe (NaN/inf/numpy scalars -> JSON types)."""
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, "item") and type(v).__module__.startswith("numpy"):
        return clean(v.item())
    return v


def safe_star(val, default: int = 3) -> int:
    """Star rating for the dashboard sample. NaN is truthy in Python, so `val or 3` is not enough."""
    try:
        if val is None or pd.isna(val):
            return default
        n = int(round(float(val)))
        return min(5, max(1, n))
    except (TypeError, ValueError):
        return default


def metrics_to_payload(metrics: dict, mode: str, name: str, category: str, reviews_n: int) -> dict:
    """Convert analyze_frame()'s output dict into the JSON shape the dashboard JS expects."""
    complaints_df = metrics["complaints"]
    likes_df = metrics["likes"]
    aspect_df = metrics["aspect"]
    word_df = metrics["word_cloud"]
    trends = metrics.get("trends") or {}
    spikes = metrics.get("spikes") or []

    def top_phrases(df, quotes, k=3):
        if df is None or len(df) == 0:
            return []
        rows = df[df["count"] > 0].head(k)
        out = []
        for _, r in rows.iterrows():
            qs = quotes.get(r["phrase"], [])
            out.append({"t": r["phrase"], "pct": round(float(r["pct_of_reviews"])), "q": qs[0] if qs else ""})
        return out

    complaints = top_phrases(complaints_df, metrics.get("complaint_quotes", {}))
    praises = top_phrases(likes_df, metrics.get("like_quotes", {}))

    aspects = (
        [{"n": r["aspect"], "p": round(float(r["positive_pct"]))} for _, r in aspect_df.head(6).iterrows()]
        if aspect_df is not None and len(aspect_df) else []
    )

    words = (
        [[r["word"], 1 if r["dominant_sentiment"] == "Positive" else (-1 if r["dominant_sentiment"] == "Negative" else 0)]
         for _, r in word_df.head(24).iterrows()]
        if word_df is not None and len(word_df) else []
    )

    monthly = trends.get("monthly_data")
    if monthly is not None and len(monthly):
        months = monthly["month"].tolist()
        trend = [round(float(x)) for x in monthly["positive_pct"].tolist()]
    else:
        months, trend = [], []

    star = metrics.get("star_alignment")
    rating_dist = [0, 0, 0, 0, 0]
    if star is not None and len(star):
        by_star = {int(r["rating_val"]): float(r["reviews"]) for _, r in star.iterrows()}
        total = sum(by_star.values()) or 1
        rating_dist = [round(100 * by_star.get(s, 0) / total) for s in [5, 4, 3, 2, 1]]

    sample = metrics["frame"].head(8)
    reviews_sample = [
        {
            "r": safe_star(row.get("rating")),
            "t": str(row["review"])[:180],
            "cat": str(row.get("category") or row.get("product") or ""),
        }
        for _, row in sample.iterrows()
    ]

    spike = None
    if spikes:
        s = spikes[0]
        spike = {
            "t": f"{s['theme']} · {s['month']}",
            "q": f"Complaint share jumped from {s['previous_share_pct']}% to {s['current_share_pct']}% month-over-month.",
        }

    payload = {
        "mode": mode,
        "name": name,
        "category": category,
        "reviews": reviews_n,
        "pos": round(metrics["positive_pct"], 1),
        "neg": round(metrics["negative_pct"], 1),
        "neu": round(metrics["neutral_pct"], 1),
        "avgRating": round(float(metrics["avg_rating"]), 1) if metrics.get("avg_rating") is not None else None,
        "complaints": complaints,
        "praises": praises,
        "aspects": aspects,
        "words": words,
        "months": months,
        "trend": trend,
        "ratingDist": rating_dist,
        "reviewsSample": reviews_sample,
        "spike": spike,
    }
    return {k: clean(v) for k, v in payload.items()}


@app.get("/")
def index():
    return send_from_directory(DASHBOARD_FILE.parent, DASHBOARD_FILE.name)


@app.get("/api/global")
def global_stats():
    kpi_path = PROCESSED / "sentiment_kpis.csv"
    if not kpi_path.exists():
        return jsonify({"error": "processed/sentiment_kpis.csv not found. Run build_dashboard_aggregates.py first."}), 404

    kpis = pd.read_csv(kpi_path).iloc[0]
    cat = pd.read_csv(PROCESSED / "category_sentiment.csv") if (PROCESSED / "category_sentiment.csv").exists() else pd.DataFrame()
    monthly = pd.read_csv(PROCESSED / "monthly_sentiment_full.csv") if (PROCESSED / "monthly_sentiment_full.csv").exists() else pd.DataFrame()
    theme_summary = pd.read_csv(PROCESSED / "theme_summary_v4.csv") if (PROCESSED / "theme_summary_v4.csv").exists() else pd.DataFrame()
    praise_sample = pd.read_csv(PROCESSED / "praise_phrases_sample.csv") if (PROCESSED / "praise_phrases_sample.csv").exists() else pd.DataFrame()
    complaint_words = pd.read_csv(PROCESSED / "complaint_wordcloud_sample.csv") if (PROCESSED / "complaint_wordcloud_sample.csv").exists() else pd.DataFrame()

    complaints, praises = [], []
    if len(theme_summary):
        top = theme_summary.sort_values("complaint_count", ascending=False).head(3)
        for _, r in top.iterrows():
            complaints.append({"t": r["theme"], "pct": round(float(r["complaint_percentage"])), "q": ""})
    if len(praise_sample):
        top = praise_sample[praise_sample["count"] > 0].head(3)
        for _, r in top.iterrows():
            complaints_col = "pct_of_reviews" if "pct_of_reviews" in praise_sample.columns else "count"
            praises.append({"t": r["phrase"], "pct": round(float(r.get("pct_of_reviews", 0))), "q": ""})

    aspects = []
    if len(cat):
        for _, r in cat.sort_values("reviews", ascending=False).head(6).iterrows():
            aspects.append({"n": r["product"], "p": round(float(r["positive_pct"]))})

    months, trend = [], []
    if len(monthly):
        tail = monthly.tail(8)
        months = tail["month"].tolist()
        trend = [round(float(x)) for x in tail["positive_pct"].tolist()]

    words = [[r.iloc[0], -1] for _, r in complaint_words.head(24).iterrows()] if len(complaint_words) else []

    payload = {
        "mode": "global",
        "title": "All Categories · Full Dataset",
        "sub": ", ".join(cat["product"].tolist()) if len(cat) else "",
        "reviews": int(kpis["total_reviews"]),
        "pos": round(float(kpis["positive_pct"]), 1),
        "neg": round(float(kpis["negative_pct"]), 1),
        "neu": round(float(kpis["neutral_pct"]), 1),
        "avgRating": round(float(kpis["avg_rating"]), 1) if pd.notna(kpis.get("avg_rating")) else None,
        "complaints": complaints,
        "praises": praises,
        "aspects": aspects,
        "words": words,
        "months": months,
        "trend": trend,
        "ratingDist": [0, 0, 0, 0, 0],
        "reviewsSample": [],
    }
    return jsonify({k: clean(v) for k, v in payload.items()})


@app.post("/api/analyze-url")
def analyze_url():
    body = request.get_json(force=True) or {}
    url = (body.get("url") or "").strip()
    if not url:
        return jsonify({"error": "Missing url"}), 400

    try:
        res = extract_reviews_from_url(url)
        metrics = analyze_frame(res["reviews_df"])
        profile = extract_product_profile(res["product_name"], reviews_df=res["reviews_df"], url_info=res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    payload = metrics_to_payload(
        metrics, mode="product",
        name=res["product_name"],
        category=profile.get("category") or res.get("product_specs", {}).get("Category", ""),
        reviews_n=res["total_reviews"],
    )
    payload["status_message"] = res["status_message"]
    payload["is_live_scraped"] = res["is_live_scraped"]
    return jsonify(payload)


@app.post("/api/analyze-csv")
def analyze_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        raw = pd.read_csv(request.files["file"])
        norm = normalize_upload(raw)
        metrics = analyze_frame(norm)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    name = request.files["file"].filename
    payload = metrics_to_payload(metrics, mode="product", name=name, category="Uploaded", reviews_n=metrics["n"])
    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
