"""
Lumina Context Manager: Builds unified, structured context snapshots
combining live product metadata, dataset vitals, dashboard page state,
analytics metrics, and user preferences.
"""

from __future__ import annotations

from typing import Any
from .data_layer import LuminaDataLayer
from .memory_manager import UserMemoryPreferences


class LuminaContextManager:
    """Assembles and optimizes product and analytical context for AI reasoning."""

    @staticmethod
    def build_context_snapshot(
        metrics: dict[str, Any] | None,
        profile: dict[str, Any] | None,
        product_name: str | None,
        active_page: str = "⚡ Overview & Intelligence",
        preferences: UserMemoryPreferences | None = None,
        active_topic: str | None = None,
    ) -> dict[str, Any]:
        """Constructs a comprehensive, grounded context dictionary."""
        prod_info = LuminaDataLayer.get_current_product_info(metrics, profile, product_name)
        dataset_vitals = LuminaDataLayer.get_dataset_vitals(metrics)
        complaints = LuminaDataLayer.get_complaints(metrics, limit=4)
        praises = LuminaDataLayer.get_positive_feedback(metrics, limit=4)
        aspects = LuminaDataLayer.get_aspect_sentiment(metrics)
        conflicts = LuminaDataLayer.get_sarcasm_and_conflicts(metrics)
        tickets = LuminaDataLayer.get_actionable_tickets(metrics, limit=2)

        return {
            "product": prod_info,
            "dataset": dataset_vitals,
            "dashboard_state": {
                "active_page": active_page,
                "active_topic": active_topic,
            },
            "analytics": {
                "top_complaints": complaints,
                "top_praises": praises,
                "aspects": aspects,
                "conflicts": conflicts,
                "actionable_tickets": tickets,
            },
            "user_preferences": {
                "detail_level": preferences.detail_level if preferences else "balanced",
                "explanation_style": preferences.explanation_style if preferences else "balanced",
                "audience_focus": preferences.audience_focus if preferences else "product",
                "auto_show_reviews": preferences.auto_show_reviews if preferences else True,
            },
        }

    @staticmethod
    def build_system_prompt(context: dict[str, Any]) -> str:
        """Constructs a concise, highly-structured system prompt incorporating Lumina data."""
        p = context["product"]
        d = context["dataset"]
        a = context["analytics"]
        dash = context["dashboard_state"]
        pref = context["user_preferences"]

        # Format complaints summary
        c_lines = []
        for c in a["top_complaints"][:3]:
            c_lines.append(f"  • {c['defect']} (Severity: {c['severity']}/100, {c['mentions']} mentions, Trend: {c['trend']})")
        comp_summary = "\n".join(c_lines) if c_lines else "  • No major systemic defects detected."

        # Format praises summary
        p_lines = []
        for pr in a["top_praises"][:3]:
            p_lines.append(f"  • {pr['praise']} ({pr['mentions']} mentions, ~{pr['pct_share']}% share)")
        praise_summary = "\n".join(p_lines) if p_lines else "  • General positive satisfaction."

        # Format aspect summary
        asp_lines = []
        for asp in a["aspects"][:4]:
            asp_lines.append(f"  • {asp['aspect']}: {asp['positive_pct']}% Pos / {asp['negative_pct']}% Neg ({asp['mentions']} clauses)")
        aspect_summary = "\n".join(asp_lines) if asp_lines else "  • Standard aspect performance."

        prompt = f"""You are Lumina AI, an advanced enterprise product intelligence and decision assistant.
You possess two integrated dimensions of intelligence:
1. GENERAL AI ASSISTANT: You can answer any general question (e.g. definitions, technology explanations, writing, comparison, science, engineering) conversationally, naturally, and accurately like ChatGPT.
2. DEEP LUMINA PRODUCT INTELLIGENCE: When the user asks about the product currently analyzed in Lumina (or uses 'this', 'it', 'this product', 'the reviews', 'customers'), you become deeply product-aware, strictly grounding claims in Lumina's actual review dataset.

CURRENT PRODUCT CONTEXT:
• Product Name: {p['name']}
• Brand: {p['brand']} | ASIN: {p['asin']} | Price: {p['price']}
• Category: {p['category']}
• Description: {p['description'][:200]}...

CURRENT REVIEW DATASET:
• Total Verified Reviews Analyzed: {d['n_reviews']:,}
• Baseline Star Rating: ⭐ {d['avg_rating']:.2f} / 5.00
• Net Sentiment: {d['positive_pct']}% Positive | {d['neutral_pct']}% Neutral | {d['negative_pct']}% Negative
• Date Range: {d['date_range']} | Simulated eNPS: {d['enps']}

CURRENT ANALYTICS:
• Top Customer Friction Areas:
{comp_summary}
• Core Growth Moats (What Buyers Love):
{praise_summary}
• Hardware & Functional Aspect Sentiment:
{aspect_summary}
• Review Authenticity & Sarcasm: {a['conflicts']['sarcasm_count']} sarcastic reviews / {a['conflicts']['mismatch_count']} rating-sentiment mismatches detected.
• Active Dashboard Screen: {dash['active_page']}

RESPONSE GUIDELINES:
- Answer general questions directly and conversationally without forcing product discussions.
- When discussing the product, ground claims in the dataset above. Never hallucinate review counts, percentages, or quotes.
- If combining general technical knowledge with Lumina data (e.g. why Bluetooth drops or how ANC works), blend technical explanations smoothly with what verified reviews report.
- Style Preference: {pref['detail_level']} detail, {pref['explanation_style']} tone, {pref['audience_focus']} focus.
- Never mention internal JSON schemas, tool names, or routing tags to the user.
"""
        return prompt
