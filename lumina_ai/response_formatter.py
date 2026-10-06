"""
Lumina Response Formatter: Generates rich, polished evidence cards,
contextual follow-up suggestions, and activity indicator traces.
"""

from __future__ import annotations

from typing import Any
from .intent_router import IntentClassification


class LuminaResponseFormatter:
    """Formats AI outputs into premium, interactive conversational experiences."""

    ASPECT_ICONS = {
        "Battery": "🔋",
        "Sound": "🎧",
        "ANC": "🔇",
        "Comfort": "☁️",
        "Connectivity": "📡",
        "Price": "💰",
        "Build": "🛠️",
        "App / Software": "📱",
        "Complaints": "⚠️",
        "Sarcasm & Conflicts": "🚨",
        "Praise": "❤️",
        "Engineering Fix": "🛠️",
        "Overview": "⚡",
        "Product Profile": "📦",
    }

    ASPECT_PAGES = {
        "Battery": ("💬 Customer Themes", "View in Customer Themes"),
        "Sound": ("💬 Customer Themes", "View in Customer Themes"),
        "ANC": ("💬 Customer Themes", "View in Customer Themes"),
        "Comfort": ("💬 Customer Themes", "View in Customer Themes"),
        "Connectivity": ("⚠️ Biggest Complaints", "View in Biggest Complaints"),
        "Price": ("🧠 Advanced AI Analyst", "View in AI Analyst"),
        "Build": ("⚠️ Biggest Complaints", "View in Biggest Complaints"),
        "App / Software": ("💬 Customer Themes", "View in Customer Themes"),
        "Complaints": ("⚠️ Biggest Complaints", "View in ⚠️ Biggest Complaints"),
        "Sarcasm & Conflicts": ("⭐ Rating vs AI Sentiment", "View in ⭐ Rating vs AI Sentiment"),
        "Praise": ("❤️ What Customers Love", "View in ❤️ What Customers Love"),
        "Engineering Fix": ("🛠️ Actionable Ticket Generator", "View in 🛠️ Actionable Ticket Generator"),
        "Overview": ("⚡ Overview & Intelligence", "View in ⚡ Overview & Intelligence"),
        "Product Profile": ("📦 Product Profile", "View in 📦 Product Profile"),
    }

    @classmethod
    def build_evidence_cards(
        cls,
        intent: IntentClassification,
        context: dict[str, Any],
        supporting_reviews: list[str],
    ) -> list[dict[str, Any]]:
        """Constructs rich, structured product evidence cards."""
        cards = []
        target_aspect = intent.target_aspect

        if target_aspect:
            icon = cls.ASPECT_ICONS.get(target_aspect, "📊")
            page_info = cls.ASPECT_PAGES.get(target_aspect, ("🔍 Review Explorer", "Explore in Review Explorer"))
            
            # Find aspect metric in context
            aspect_stats = next(
                (a for a in context.get("analytics", {}).get("aspects", []) if a.get("aspect") == target_aspect),
                None
            )
            
            quotes = supporting_reviews[:2]

            if target_aspect == "Product Profile":
                prod = context.get("product", {})
                brand = prod.get("brand", "Unknown Brand")
                price = prod.get("price", "N/A")
                cat = prod.get("category", "Electronics")
                asin = prod.get("asin", "N/A")
                desc = prod.get("description") or prod.get("tagline") or ""
                quote_list = [desc[:160] + "..."] if desc else []
                cards.append({
                    "type": "product_profile_card",
                    "title": f"📦 {prod.get('name', 'Product Profile')}",
                    "stat_line": f"Brand: {brand} · Price: {price}",
                    "sub_stat": f"Category: {cat} · ASIN: {asin}",
                    "quotes": quote_list,
                    "redirect_page": "📦 Product Profile",
                    "redirect_label": "👉 View in 📦 Product Profile",
                })
                return cards
            elif target_aspect == "Complaints":
                top_c_list = context.get("analytics", {}).get("top_complaints", [])
                if top_c_list:
                    c0 = top_c_list[0]
                    stat_line = f"Top Defect: {c0.get('defect')}"
                    mentions_line = f"Severity: {c0.get('severity')}/100 · {c0.get('mentions')} mentions"
                    if not quotes and c0.get("quotes"):
                        quotes = c0.get("quotes")[:2]
                else:
                    stat_line = "No severe systemic defects detected"
                    mentions_line = "Verified Review Citations"
            elif target_aspect == "Sarcasm & Conflicts":
                conf = context.get("analytics", {}).get("conflicts", {})
                sarc = conf.get("sarcasm_count", 0)
                hjk = conf.get("mismatch_count", 0)
                stat_line = f"{sarc} Sarcastic Reviews · {hjk} 5★ Hijacks"
                mentions_line = "Rating vs AI Sentiment Mismatch Audit"
                if not quotes and conf.get("examples"):
                    quotes = conf.get("examples")[:2]
            elif target_aspect == "Praise":
                top_p_list = context.get("analytics", {}).get("top_praises", [])
                if top_p_list:
                    p0 = top_p_list[0]
                    stat_line = f"Core Moat: {p0.get('praise')}"
                    mentions_line = f"{p0.get('mentions')} mentions · ~{p0.get('pct_share')}% share"
                    if not quotes and p0.get("quotes"):
                        quotes = p0.get("quotes")[:2]
                else:
                    stat_line = "Organic Customer Advocacy"
                    mentions_line = "Verified Review Citations"
            else:
                stat_line = f"{aspect_stats['positive_pct']}% Positive / {aspect_stats['negative_pct']}% Negative" if aspect_stats else "Cited across verified reviews"
                mentions_line = f"Based on {aspect_stats['mentions']} customer clauses" if aspect_stats else "Verified Review Citations"

            cards.append({
                "type": "aspect_card",
                "title": f"{icon} {target_aspect}",
                "stat_line": stat_line,
                "sub_stat": mentions_line,
                "quotes": quotes,
                "redirect_page": page_info[0],
                "redirect_label": f"👉 {page_info[1]}",
            })

        # If general product review analysis without single aspect, show top complaint card
        elif intent.category in ["REVIEW_ANALYSIS", "FOLLOW_UP"] and context.get("analytics", {}).get("top_complaints"):
            top_c = context["analytics"]["top_complaints"][0]
            cards.append({
                "type": "complaint_card",
                "title": f"⚠️ Top Customer Friction: {top_c['defect']}",
                "stat_line": f"Severity Score: {top_c['severity']}/100",
                "sub_stat": f"{top_c['mentions']} mentions · {top_c['trend']} velocity",
                "quotes": top_c.get("quotes", [])[:2],
                "redirect_page": "⚠️ Biggest Complaints",
                "redirect_label": "👉 View in ⚠️ Biggest Complaints",
            })

        return cards

    @classmethod
    def generate_followup_suggestions(
        cls,
        intent: IntentClassification,
        context: dict[str, Any],
        product_name: str,
    ) -> list[str]:
        """Generates dynamic, highly contextual follow-up chips."""
        aspect = intent.target_aspect
        top_complaints = context.get("analytics", {}).get("top_complaints") or []
        top_complaint = top_complaints[0].get("defect", "complaints") if top_complaints else "complaints"

        if aspect == "Product Profile":
            return [
                "What is the biggest problem customers have with this product?",
                "What do customers love most about it?",
                "How is the battery life and sound quality?",
                "Is this product worth the price?",
            ]

        if aspect and aspect not in ["Complaints", "Sarcasm & Conflicts", "Praise", "Overview", "Product Profile"]:
            return [
                f"Show verified quotes on {aspect}",
                f"Are {aspect} complaints getting worse?",
                f"Compare {aspect} with Bose",
                f"Create a P0 ticket for {aspect}",
            ]

        if aspect == "Complaints":
            return [
                f"Create a P0 engineering ticket for {top_complaint}",
                "Who is most affected by these complaints?",
                "Are there any sarcastic 5-star reviews?",
                "What do customers love most?",
            ]

        if aspect == "Sarcasm & Conflicts":
            return [
                "Show me the top customer complaints",
                "What is the clean star rating without hijacks?",
                "Create a P0 ticket for the worst complaint",
            ]

        if intent.category == "COMPARISON":
            target = intent.comparison_target or "Bose"
            return [
                f"Which one has better sound quality?",
                f"Which one is more comfortable?",
                f"Is the price difference justified?",
            ]

        if intent.category in ["REVIEW_ANALYSIS", "PRODUCT"]:
            return [
                f"Why are people unhappy with {top_complaint}?",
                "Is this product actually worth buying?",
                "Are there any sarcastic 5-star reviews?",
                "Compare this with Bose",
            ]

        # General suggestions
        return [
            f"How does this apply to {product_name}?",
            "What do verified buyers say about this?",
            "Show me the top customer complaints",
        ]
