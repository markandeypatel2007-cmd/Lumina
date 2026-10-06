"""
Lumina Data Layer: Clean tool/data access layer interfacing directly with
Lumina's existing review analysis, aspect matrices, complaints, and profiles.
Reuses existing functions and data structures without rebuilding analytics.
"""

from __future__ import annotations

import re
from typing import Any
import pandas as pd


class LuminaDataLayer:
    """Provides structured, safe read access to Lumina's active analytics and review corpus."""

    @staticmethod
    def get_current_product_info(metrics: dict[str, Any] | None, profile: dict[str, Any] | None, product_name: str | None) -> dict[str, Any]:
        """Extracts current product identity, specs, and price."""
        p_name = product_name or "Selected Product"
        brand = "Unknown"
        asin = "N/A"
        category = "Electronics"
        tagline = ""
        description = ""
        specs: dict[str, str] = {}
        price = "N/A"
        image = ""

        if not profile or not isinstance(profile, dict) or not profile.get("specs"):
            try:
                from product_profile import extract_product_profile
                profile = extract_product_profile(p_name)
            except Exception:
                pass

        if profile and isinstance(profile, dict):
            p_name = profile.get("name") or profile.get("product_name") or p_name
            brand = profile.get("brand") or brand
            asin = profile.get("asin") or asin
            category = profile.get("category") or category
            tagline = profile.get("tagline") or ""
            description = profile.get("description") or ""
            specs = profile.get("specs") or {}
            price = profile.get("price") or profile.get("product_price") or price
            image = profile.get("image") or ""

        return {
            "name": p_name,
            "brand": brand,
            "asin": asin,
            "category": category,
            "tagline": tagline,
            "description": description,
            "specs": specs,
            "price": price,
            "image": image,
        }

    @staticmethod
    def get_dataset_vitals(metrics: dict[str, Any] | None) -> dict[str, Any]:
        """Returns baseline dataset metrics: count, ratings, net sentiment."""
        if not metrics or not isinstance(metrics, dict):
            return {
                "n_reviews": 0,
                "avg_rating": 0.0,
                "positive_pct": 0.0,
                "neutral_pct": 0.0,
                "negative_pct": 0.0,
                "date_range": "N/A",
                "enps": 0,
            }

        n = metrics.get("n", 0)
        pos = metrics.get("positive_pct", 0.0)
        neu = metrics.get("neutral_pct", 0.0)
        neg = metrics.get("negative_pct", 0.0)
        avg_r = metrics.get("avg_rating", 0.0) or 0.0

        frame = metrics.get("frame")
        date_str = "All Time"
        if frame is not None and not frame.empty and "reviewTime" in frame.columns:
            try:
                valid_dates = pd.to_datetime(frame["reviewTime"], errors="coerce").dropna()
                if not valid_dates.empty:
                    date_str = f"{valid_dates.min().strftime('%b %Y')} - {valid_dates.max().strftime('%b %Y')}"
            except Exception:
                pass

        enps = int(round(pos - neg))

        return {
            "n_reviews": n,
            "avg_rating": round(float(avg_r), 2),
            "positive_pct": round(float(pos), 1),
            "neutral_pct": round(float(neu), 1),
            "negative_pct": round(float(neg), 1),
            "date_range": date_str,
            "enps": enps,
        }

    @staticmethod
    def search_reviews(
        metrics: dict[str, Any] | None,
        query: str,
        limit: int = 4,
        sentiment: str | None = None,
        max_rating: float | None = None,
        min_rating: float | None = None,
    ) -> list[dict[str, Any]]:
        """Searches customer reviews in the frame matching query tokens and optional filters."""
        if not metrics or "frame" not in metrics:
            return []

        frame: pd.DataFrame = metrics["frame"]
        if frame is None or frame.empty or "review" not in frame.columns:
            return []

        subset = frame

        if sentiment and "sentiment" in subset.columns:
            subset = subset[subset["sentiment"].astype(str).str.lower() == sentiment.lower()]

        if "rating" in subset.columns:
            if max_rating is not None:
                subset = subset[subset["rating"] <= max_rating]
            if min_rating is not None:
                subset = subset[subset["rating"] >= min_rating]

        # Extract search tokens
        stop_words = {
            "what", "is", "the", "are", "they", "does", "do", "how", "can", "i", "you",
            "this", "that", "these", "for", "and", "or", "in", "on", "at", "to", "a", "an",
            "about", "product", "review", "reviews", "customer", "customers", "tell", "me",
            "there", "their", "from", "when", "where", "which", "will", "would", "could",
        }
        tokens = [re.sub(r"[^a-zA-Z0-9]", "", w.lower()) for w in query.split()]
        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]

        if tokens:
            pattern = "|".join([re.escape(t) for t in tokens])
            try:
                matched = subset[subset["review"].astype(str).str.contains(pattern, case=False, na=False)]
            except Exception:
                matched = subset
        else:
            matched = subset

        results = []
        for _, row in matched.head(limit).iterrows():
            text = str(row.get("review", ""))[:320]
            rating = row.get("rating", "N/A")
            sent = row.get("sentiment", "Neutral")
            date = str(row.get("reviewTime", ""))
            results.append({
                "review": text,
                "rating": rating,
                "sentiment": sent,
                "date": date,
            })
        return results

    @staticmethod
    def get_complaints(metrics: dict[str, Any] | None, limit: int = 5) -> list[dict[str, Any]]:
        """Returns top customer friction areas with severity, mentions, and quotes."""
        if not metrics:
            return []

        severities = metrics.get("severity") or []
        complaint_quotes = metrics.get("complaint_quotes") or {}

        results = []
        if isinstance(severities, list) and severities:
            for item in severities[:limit]:
                defect = item.get("defect") or item.get("complaint") or "General Friction"
                score = item.get("severity_score", 50)
                mentions = item.get("mentions", 0)
                trend = item.get("recency_trend", "Stable")
                root = item.get("root_cause", "Component friction reported in reviews.")
                quotes = complaint_quotes.get(defect, [])[:2]
                results.append({
                    "defect": defect,
                    "severity": score,
                    "mentions": mentions,
                    "trend": trend,
                    "root_cause": root,
                    "quotes": quotes,
                })
        elif "complaints" in metrics and isinstance(metrics["complaints"], pd.DataFrame) and not metrics["complaints"].empty:
            df: pd.DataFrame = metrics["complaints"]
            for _, row in df.head(limit).iterrows():
                defect = row.get("complaint", "General Issue")
                mentions = row.get("count", 0)
                pct = row.get("pct_of_reviews", 0)
                quotes = complaint_quotes.get(defect, [])[:2]
                results.append({
                    "defect": defect,
                    "severity": int(pct * 2.5) if pct else 45,
                    "mentions": mentions,
                    "trend": "Stable",
                    "root_cause": "Issue cited across negative customer feedback.",
                    "quotes": quotes,
                })
        return results

    @staticmethod
    def get_positive_feedback(metrics: dict[str, Any] | None, limit: int = 5) -> list[dict[str, Any]]:
        """Returns top praised features (growth moats) and quotes."""
        if not metrics:
            return []

        likes_df = metrics.get("likes")
        like_quotes = metrics.get("like_quotes") or {}

        results = []
        if isinstance(likes_df, pd.DataFrame) and not likes_df.empty:
            for _, row in likes_df.head(limit).iterrows():
                praise = row.get("praise") or row.get("feature") or "Quality"
                mentions = row.get("count", 0)
                pct = row.get("pct_of_reviews", 0)
                quotes = like_quotes.get(praise, [])[:2]
                results.append({
                    "praise": praise,
                    "mentions": mentions,
                    "pct_share": pct,
                    "quotes": quotes,
                })
        return results

    @staticmethod
    def get_aspect_sentiment(metrics: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Returns breakdown across key hardware/functional aspects (Battery, Sound, Comfort, etc.)."""
        if not metrics:
            return []

        aspect_df = metrics.get("aspect")
        if isinstance(aspect_df, pd.DataFrame) and not aspect_df.empty:
            results = []
            for _, row in aspect_df.head(8).iterrows():
                aspect_name = row.get("aspect", "Aspect")
                pos_pct = row.get("positive_pct", 50.0)
                neg_pct = row.get("negative_pct", 30.0)
                neu_pct = row.get("neutral_pct", 20.0)
                total = row.get("total_clauses") or row.get("mentions") or 0
                results.append({
                    "aspect": aspect_name,
                    "positive_pct": round(float(pos_pct), 1),
                    "negative_pct": round(float(neg_pct), 1),
                    "neutral_pct": round(float(neu_pct), 1),
                    "mentions": int(total),
                })
            return results
        return []

    @staticmethod
    def get_sarcasm_and_conflicts(metrics: dict[str, Any] | None) -> dict[str, Any]:
        """Detects 5-star visibility hijacks and sarcastic reviews."""
        if not metrics:
            return {"sarcasm_count": 0, "mismatch_count": 0, "examples": []}

        sarcasm_cnt = metrics.get("sarcasm_count", 0)
        mismatches = metrics.get("mismatch_high_star", [])
        examples = []
        for m in mismatches[:3]:
            if isinstance(m, dict) and m.get("review"):
                examples.append(str(m["review"])[:200])

        return {
            "sarcasm_count": sarcasm_cnt,
            "mismatch_count": len(mismatches),
            "examples": examples,
        }

    @staticmethod
    def get_actionable_tickets(metrics: dict[str, Any] | None, limit: int = 3) -> list[dict[str, Any]]:
        """Returns auto-generated sprint engineering work orders."""
        if not metrics:
            return []
        tickets = metrics.get("actionable_tickets") or []
        res = []
        for t in tickets[:limit]:
            res.append({
                "priority": t.get("priority", "P0"),
                "title": t.get("title", "Hardware Remediation"),
                "subsystem": t.get("subsystem", "Hardware/QA"),
                "star_lift": t.get("star_lift") or t.get("estimated_star_lift", "+0.25★"),
                "complaint_source": t.get("complaint_source", "Customer Friction"),
            })
        return res

    @staticmethod
    def get_supporting_evidence_for_topic(metrics: dict[str, Any] | None, topic: str, limit: int = 3) -> list[str]:
        """Finds direct verbatim customer citations for an issue or feature."""
        if not metrics:
            return []

        comp_quotes = metrics.get("complaint_quotes") or {}
        like_quotes = metrics.get("like_quotes") or {}

        # Check exact key matches
        for k, q_list in comp_quotes.items():
            if topic.lower() in k.lower() or k.lower() in topic.lower():
                return q_list[:limit]
        for k, q_list in like_quotes.items():
            if topic.lower() in k.lower() or k.lower() in topic.lower():
                return q_list[:limit]

        # Fallback to search_reviews
        search_hits = LuminaDataLayer.search_reviews(metrics, topic, limit=limit)
        return [h["review"] for h in search_hits]
