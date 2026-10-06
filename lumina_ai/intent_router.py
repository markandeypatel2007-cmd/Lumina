"""
Lumina Intent Router: Classifies queries into intelligent analytical categories
and extracts key entities/aspects without exposing classifications to the user.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class IntentClassification:
    category: str              # GENERAL, PRODUCT, REVIEW_ANALYSIS, DATA_ANALYSIS, COMPARISON, FOLLOW_UP, MIXED
    target_aspect: str | None  # Battery, Sound, Comfort, Connectivity, Price, etc.
    is_product_specific: bool
    requires_reviews: bool
    comparison_target: str | None = None
    activity_steps: list[str] | None = None


class LuminaIntentRouter:
    """Intelligent classification and entity routing layer."""

    ASPECT_KEYWORDS = {
        "Battery": ["battery", "charge", "charging", "charger", "drain", "draining", "power"],
        "Sound": ["sound", "audio", "bass", "treble", "volume", "music", "acoustic", "mic", "microphone"],
        "ANC": ["anc", "noise cancel", "noise cancellation", "ambient", "transparency"],
        "Comfort": ["comfort", "comfortable", "fit", "ear pad", "headband", "heavy", "tight", "hurts", "glasses", "uncomfortable"],
        "Connectivity": ["bluetooth", "wifi", "connect", "connection", "disconnect", "pairing", "range"],
        "Price": ["price", "cost", "expensive", "cheap", "worth", "value", "money", "overpriced"],
        "Build": ["build", "durability", "hinge", "plastic", "break", "broken", "material", "sturdy", "flimsy"],
        "App / Software": ["app", "software", "firmware", "update", "ios", "android"],
    }

    @classmethod
    def classify(
        cls,
        query: str,
        current_product_name: str | None = None,
        active_topic: str | None = None,
        has_previous_turns: bool = False,
    ) -> IntentClassification:
        q_low = query.lower().strip()
        activity = ["✦ Understanding inquiry"]

        # 1. Identify Target Aspect if mentioned
        detected_aspect = None
        for asp, kws in cls.ASPECT_KEYWORDS.items():
            if any(k in q_low for k in kws):
                detected_aspect = asp
                break

        # 2. Check for Product Identity, Specs & Metadata
        if any(p in q_low for p in [
            "what is the product", "what is this product", "which product", "what product",
            "tell me about the product", "about this product", "product name", "product profile",
            "product details", "product info", "specs", "specifications", "spec", "dimension",
            "weight", "asin", "brand", "model"
        ]):
            activity.append("✓ Retrieved active product identity & specifications")
            return IntentClassification(
                category="PRODUCT",
                target_aspect="Product Profile",
                is_product_specific=True,
                requires_reviews=False,
                activity_steps=activity,
            )

        # 3. Check for Sarcasm & 5-Star Conflict Analysis
        if any(k in q_low for k in ["sarcas", "sarcastic", "hijack", "fake", "conflict", "5 star", "5-star", "5★", "ironic", "mismatch", "trick"]):
            activity.append("✓ Audited review conflicts, 5★ hijacks & sarcasm")
            return IntentClassification(
                category="REVIEW_ANALYSIS",
                target_aspect=detected_aspect or "Sarcasm & Conflicts",
                is_product_specific=True,
                requires_reviews=True,
                activity_steps=activity,
            )

        # 3. Check for Complaints & Critical Feedback
        if any(w in q_low for w in ["complaint", "complaints", "problem", "problems", "issue", "issues", "defect", "defects", "friction", "worst", "unhappy", "critic", "return", "refund", "broken", "failing"]):
            activity.append(f"✓ Scanned review dataset for customer friction on '{detected_aspect or 'product'}'")
            return IntentClassification(
                category="REVIEW_ANALYSIS",
                target_aspect=detected_aspect or "Complaints",
                is_product_specific=True,
                requires_reviews=True,
                activity_steps=activity,
            )

        # 4. Check for Praise & Moats
        if any(w in q_low for w in ["praise", "love", "like", "best", "strength", "strengths", "delight", "favorite", "positives", "pros"]):
            activity.append(f"✓ Scanned review dataset for praised features on '{detected_aspect or 'product'}'")
            return IntentClassification(
                category="REVIEW_ANALYSIS",
                target_aspect=detected_aspect or "Praise",
                is_product_specific=True,
                requires_reviews=True,
                activity_steps=activity,
            )

        # 5. Check for Actionable Tickets & Engineering Fixes
        if any(w in q_low for w in ["ticket", "work order", "jira", "engineering fix", "p0", "p1", "sprint", "remediation"]):
            activity.append("✓ Retrieved sprint engineering work orders")
            return IntentClassification(
                category="DATA_ANALYSIS",
                target_aspect=detected_aspect or "Engineering Fix",
                is_product_specific=True,
                requires_reviews=False,
                activity_steps=activity,
            )

        # 6. Check for Comparisons
        comp_match = re.search(r"\b(compare|vs|versus|better than|against)\b\s+([a-zA-Z0-9\s]+)", q_low)
        comparison_target = None
        if comp_match:
            raw_target = comp_match.group(2).strip()
            for w in ["this", "that", "the", "other"]:
                raw_target = re.sub(rf"\b{w}\b", "", raw_target).strip()
            if raw_target:
                comparison_target = raw_target.title()

        if comparison_target or "compare" in q_low:
            activity.append(f"✓ Identified comparison request vs '{comparison_target or 'competitors'}'")
            return IntentClassification(
                category="COMPARISON",
                target_aspect=detected_aspect,
                is_product_specific=True,
                requires_reviews=True,
                comparison_target=comparison_target,
                activity_steps=activity,
            )

        # 7. Check for Short Follow-ups
        is_follow_up = False
        if has_previous_turns:
            if len(q_low.split()) <= 4 and (
                q_low in ["why?", "why", "how so?", "which one?", "worst one?", "show reviews", "prove it", "more", "details"]
                or q_low.startswith(("which", "show", "what about", "is it", "and", "why"))
            ):
                is_follow_up = True
            elif any(w in q_low for w in ["which one is worst", "which is worst", "show me those reviews", "are newer customers"]):
                is_follow_up = True

        if is_follow_up:
            activity.append(f"✓ Context resolved to prior topic: '{active_topic or 'product complaints'}'")
            return IntentClassification(
                category="FOLLOW_UP",
                target_aspect=detected_aspect or active_topic,
                is_product_specific=True,
                requires_reviews=True,
                activity_steps=activity,
            )

        # 8. Check if query is explicitly or implicitly product-specific
        product_indicators = [
            "this", "these", "the product", "this product", "this headphone", "this item",
            "people", "customers", "buyers", "review", "reviews", "complain", "complaining",
            "worth buying", "worth it", "rating", "sentiment", "refund", "return", "overview"
        ]
        if current_product_name and current_product_name.lower() in q_low:
            is_prod_ref = True
        else:
            is_prod_ref = any(ind in q_low for ind in product_indicators)

        # 9. Check for Data Analysis (sentiment stats, rating counts, eNPS)
        if any(w in q_low for w in ["sentiment distribution", "how many reviews", "net sentiment", "rating breakdown", "enps"]):
            activity.append("✓ Retrieved corpus dataset vitals")
            return IntentClassification(
                category="DATA_ANALYSIS",
                target_aspect=detected_aspect,
                is_product_specific=True,
                requires_reviews=False,
                activity_steps=activity,
            )

        # 10. Check for Mixed Intent (e.g. "Why might customers be having battery drain issues?")
        if ("why" in q_low or "how" in q_low or "explain" in q_low) and detected_aspect and is_prod_ref:
            activity.append(f"✓ Grounded technical query in customer reviews for '{detected_aspect}'")
            return IntentClassification(
                category="MIXED",
                target_aspect=detected_aspect,
                is_product_specific=True,
                requires_reviews=True,
                activity_steps=activity,
            )

        # 11. Check for General Review Analysis on product
        if is_prod_ref and detected_aspect:
            activity.append(f"✓ Scanned review dataset for customer feedback on '{detected_aspect}'")
            return IntentClassification(
                category="REVIEW_ANALYSIS",
                target_aspect=detected_aspect,
                is_product_specific=True,
                requires_reviews=True,
                activity_steps=activity,
            )

        # 12. Product Specs / Identity
        if is_prod_ref and any(w in q_low for w in ["spec", "dimension", "weight", "price", "asin", "brand", "model", "features"]):
            activity.append("✓ Retrieved product specifications & metadata")
            return IntentClassification(
                category="PRODUCT",
                target_aspect=detected_aspect,
                is_product_specific=True,
                requires_reviews=False,
                activity_steps=activity,
            )

        # 13. Default: GENERAL (e.g. "What is Bluetooth?", "What does ANC mean?", "Write a poem", "How to brew coffee?")
        activity.append("✓ Generating general conversational response")
        return IntentClassification(
            category="GENERAL",
            target_aspect=detected_aspect,
            is_product_specific=False,
            requires_reviews=False,
            activity_steps=activity,
        )
