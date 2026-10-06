"""
Lumina Memory & Personalization Manager.
Maintains short-term conversational context (multi-turn entity resolution)
and long-term user personalization preferences with transparent user controls.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class UserMemoryPreferences:
    """User-controlled response style and personalization preferences."""
    detail_level: str = "balanced"         # "concise", "balanced", "detailed"
    explanation_style: str = "balanced"    # "simple", "balanced", "technical"
    audience_focus: str = "product"        # "product", "business_executive", "general"
    auto_show_reviews: bool = True         # whether to automatically attach review quotes
    proactive_suggestions: bool = True     # whether to suggest follow-up investigations
    memory_enabled: bool = True            # master toggle for personalization memory
    remembered_notes: list[str] = field(default_factory=list)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    role: str                              # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    intent: str | None = None
    topic: str | None = None
    evidence_cards: list[dict[str, Any]] = field(default_factory=list)
    followup_suggestions: list[str] = field(default_factory=list)
    activity_log: list[str] = field(default_factory=list)


class ConversationMemory:
    """Manages conversational history, short-term entity tracking, and preference learning."""

    def __init__(self, session_id: str = "default_session", memory_file: Path | None = None):
        self.session_id = session_id
        self.memory_file = memory_file or (Path.home() / ".lumina_ai_memory.json")
        self.preferences = self._load_preferences()
        self.turns: list[ConversationTurn] = []
        
        # Short-term entity tracking
        self.active_product: str | None = None
        self.active_topic: str | None = None
        self.active_aspect: str | None = None
        self.last_complaints_list: list[str] = []
        self.last_praise_list: list[str] = []
        self.active_comparison_target: str | None = None

    def _load_preferences(self) -> UserMemoryPreferences:
        """Loads preferences from disk if available, otherwise defaults."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return UserMemoryPreferences(**data)
        except Exception:
            pass
        return UserMemoryPreferences()

    def save_preferences(self) -> None:
        """Persists preferences to local disk safely."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.preferences), f, indent=2)
        except Exception:
            pass

    def add_user_turn(self, query: str) -> None:
        """Records a user query and learns subtle preferences."""
        self.turns.append(ConversationTurn(role="user", content=query))
        if self.preferences.memory_enabled:
            q_low = query.lower()
            if any(k in q_low for k in ["quote", "evidence", "verbatim", "show review", "prove"]):
                if "Prefers verified customer evidence" not in self.preferences.remembered_notes:
                    self.preferences.remembered_notes.append("Prefers verified customer evidence")
                    self.preferences.auto_show_reviews = True
                    self.save_preferences()
            elif any(k in q_low for k in ["brief", "short", "quick", "one sentence", "tldr"]):
                if self.preferences.detail_level != "concise":
                    self.preferences.detail_level = "concise"
                    self.save_preferences()
            elif any(k in q_low for k in ["deep", "thorough", "comprehensive", "detailed", "breakdown"]):
                if self.preferences.detail_level != "detailed":
                    self.preferences.detail_level = "detailed"
                    self.save_preferences()

    def add_assistant_turn(
        self,
        content: str,
        intent: str | None = None,
        topic: str | None = None,
        evidence_cards: list[dict[str, Any]] | None = None,
        followup_suggestions: list[str] | None = None,
        activity_log: list[str] | None = None,
    ) -> None:
        """Records assistant response and updates entity tracking."""
        self.turns.append(ConversationTurn(
            role="assistant",
            content=content,
            intent=intent,
            topic=topic,
            evidence_cards=evidence_cards or [],
            followup_suggestions=followup_suggestions or [],
            activity_log=activity_log or [],
        ))
        if topic:
            self.active_topic = topic

    def get_recent_history(self, max_turns: int = 8) -> list[dict[str, str]]:
        """Returns clean role/content message list for prompt grounding."""
        recent = self.turns[-max_turns:]
        return [{"role": t.role, "content": t.content} for t in recent]

    def resolve_references(self, query: str, active_product_name: str | None) -> tuple[str, str | None]:
        """
        Resolves pronouns ('it', 'this', 'that one', 'those reviews', 'which is worst')
        into grounded entities based on conversation context.
        Returns (augmented_query, resolved_entity).
        """
        q_low = query.lower().strip()
        resolved_entity = self.active_topic

        # If user asks "which one is the worst?", resolve to the previous complaints
        if any(p in q_low for p in ["which one is worst", "which is the worst", "which is worst", "worst one"]):
            if self.last_complaints_list:
                return f"Which of these complaints is the worst: {', '.join(self.last_complaints_list[:3])}?", self.last_complaints_list[0]

        # Pronoun "it" or "this" referring to active topic
        if re.search(r"\b(it|this|that|that issue|that defect)\b", q_low):
            if self.active_topic and not any(p in q_low for p in ["this product", "this headphone", "this item"]):
                resolved_entity = self.active_topic

        # References to "recent reviews"
        if "recent" in q_low and self.active_topic:
            return f"{query} regarding {self.active_topic}", self.active_topic

        return query, resolved_entity

    def clear_history(self) -> None:
        """Clears short-term conversational turns."""
        self.turns = []
        self.active_topic = None
        self.active_aspect = None
        self.last_complaints_list = []
        self.last_praise_list = []
        self.active_comparison_target = None

    def clear_personalization_memory(self) -> None:
        """Purges remembered user notes while preserving default settings."""
        self.preferences.remembered_notes = []
        self.save_preferences()
