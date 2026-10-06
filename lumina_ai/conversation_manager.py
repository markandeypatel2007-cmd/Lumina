"""
Lumina Conversation Manager: Orchestrates the end-to-end conversational pipeline,
multi-thread session management, memory integration, and data grounding.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date, timedelta
from typing import Any
import pandas as pd

from .context_manager import LuminaContextManager
from .data_layer import LuminaDataLayer
from .intent_router import LuminaIntentRouter, IntentClassification
from .llm_provider import get_llm_provider, BaseLLMProvider
from .memory_manager import ConversationMemory, UserMemoryPreferences
from .response_formatter import LuminaResponseFormatter


class LuminaConversationManager:
    """Manages conversations, session histories, and end-to-end query execution."""

    def __init__(self, provider: BaseLLMProvider | None = None):
        self.provider = provider or get_llm_provider()
        self.sessions: dict[str, ConversationMemory] = {}
        self.session_metadata: dict[str, dict[str, Any]] = {}
        self.active_session_id: str = self.create_session("New Investigation")

    def create_session(self, title: str = "New Investigation") -> str:
        """Initializes a new isolated conversation session."""
        session_id = str(uuid.uuid4())[:8]
        memory = ConversationMemory(session_id=session_id)
        self.sessions[session_id] = memory
        self.session_metadata[session_id] = {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.active_session_id = session_id
        return session_id

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Renames an existing session thread."""
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["title"] = new_title.strip()

    def delete_session(self, session_id: str) -> None:
        """Deletes a conversation session thread."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        if self.active_session_id == session_id:
            if self.sessions:
                self.active_session_id = list(self.sessions.keys())[0]
            else:
                self.create_session("New Investigation")

    def get_grouped_sessions(self) -> dict[str, list[dict[str, Any]]]:
        """Groups conversations by 'Today', 'Yesterday', 'Previous'."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        groups: dict[str, list[dict[str, Any]]] = {
            "Today": [],
            "Yesterday": [],
            "Previous": [],
        }

        for s_id, meta in sorted(
            self.session_metadata.items(),
            key=lambda item: item[1]["updated_at"],
            reverse=True
        ):
            try:
                dt = datetime.fromisoformat(meta["updated_at"]).date()
                if dt == today:
                    groups["Today"].append(meta)
                elif dt == yesterday:
                    groups["Yesterday"].append(meta)
                else:
                    groups["Previous"].append(meta)
            except Exception:
                groups["Previous"].append(meta)

        return groups

    def get_active_memory(self) -> ConversationMemory:
        """Returns memory of currently active session."""
        if self.active_session_id not in self.sessions:
            self.create_session()
        return self.sessions[self.active_session_id]

    def ask(
        self,
        query: str,
        metrics: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        product_name: str | None = None,
        active_page: str = "⚡ Overview & Intelligence",
    ) -> dict[str, Any]:
        """
        Executes an end-to-end grounded query turn.
        Combines conversational reasoning with live Lumina product facts.
        """
        memory = self.get_active_memory()
        prod_name = product_name or "Active Product"

        # 1. Resolve references and pronouns ('it', 'this', 'those reviews')
        resolved_query, resolved_entity = memory.resolve_references(query, prod_name)

        # 2. Intelligent Routing & Entity Classification
        intent: IntentClassification = LuminaIntentRouter.classify(
            query=resolved_query,
            current_product_name=prod_name,
            active_topic=resolved_entity or memory.active_topic,
            has_previous_turns=len(memory.turns) > 0,
        )

        activity_log = intent.activity_steps or ["✦ Understanding question"]

        # 3. Retrieve Supporting Evidence
        supporting_reviews = []
        if intent.is_product_specific and metrics:
            topic_to_search = intent.target_aspect or memory.active_topic or resolved_entity or "complaint"
            supporting_reviews = LuminaDataLayer.get_supporting_evidence_for_topic(metrics, topic_to_search, limit=3)
            if supporting_reviews:
                activity_log.append(f"✓ Retrieved {len(supporting_reviews)} customer evidence excerpts")

        # 4. Build Grounded Context Snapshot
        context = LuminaContextManager.build_context_snapshot(
            metrics=metrics,
            profile=profile,
            product_name=prod_name,
            active_page=active_page,
            preferences=memory.preferences,
            active_topic=intent.target_aspect or memory.active_topic,
        )

        # 5. Build System Prompt & Messages History
        system_prompt = LuminaContextManager.build_system_prompt(context)
        recent_messages = memory.get_recent_history(max_turns=6)
        recent_messages.append({"role": "user", "content": resolved_query})

        # 6. Generate Response via Pluggable LLM Provider
        activity_log.append("✓ Synthesizing evidence-grounded response")
        try:
            raw_response = self.provider.generate(system_prompt=system_prompt, messages=recent_messages, context=context)
        except Exception as e:
            raw_response = f"I encountered an error generating the response: {e}"

        # 7. Build Rich Evidence Cards & Dynamic Suggestions
        evidence_cards = LuminaResponseFormatter.build_evidence_cards(intent, context, supporting_reviews)
        suggestions = LuminaResponseFormatter.generate_followup_suggestions(intent, context, prod_name)

        # 8. Record in Memory & Update Metadata
        memory.add_user_turn(query)
        memory.add_assistant_turn(
            content=raw_response,
            intent=intent.category,
            topic=intent.target_aspect or resolved_entity,
            evidence_cards=evidence_cards,
            followup_suggestions=suggestions,
            activity_log=activity_log,
        )

        # Auto-title session if this is the first turn
        if len(memory.turns) <= 2 and self.active_session_id in self.session_metadata:
            auto_title = query.strip()
            if len(auto_title) > 32:
                auto_title = auto_title[:32] + "..."
            self.session_metadata[self.active_session_id]["title"] = auto_title
            self.session_metadata[self.active_session_id]["updated_at"] = datetime.now().isoformat()

        return {
            "query": query,
            "resolved_query": resolved_query,
            "response": raw_response,
            "intent": intent.category,
            "evidence_cards": evidence_cards,
            "followup_suggestions": suggestions,
            "activity_log": activity_log,
        }


# Global / session cache singleton helper
_GLOBAL_MANAGER: LuminaConversationManager | None = None


def get_conversation_manager() -> LuminaConversationManager:
    """Returns or creates the singleton LuminaConversationManager."""
    global _GLOBAL_MANAGER
    if _GLOBAL_MANAGER is None:
        _GLOBAL_MANAGER = LuminaConversationManager()
    return _GLOBAL_MANAGER
