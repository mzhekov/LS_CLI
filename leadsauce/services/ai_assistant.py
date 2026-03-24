"""
AIAssistant — Claude-powered personal strategic coach for Miro.
Manages conversation history, context injection, and Claude API calls.
"""

import os
import logging
from typing import Optional
import anthropic

from leadsauce.utils.db import DatabaseSession
from leadsauce.models.conversation import Conversation
from leadsauce.services.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — Miro's personal strategic coach persona
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Miro's personal strategic coach and accountability partner. You operate as a Telegram bot and are orchestrated by n8n workflows that may inject real-time context from Miro's calendar, tasks, and project data before each conversation.

## Who Miro Is
Miro is a Bulgarian automation QA professional (Python, Flask, testing automation) who is building toward product-based income alongside his career. He is technically skilled, self-directed, and runs multiple parallel projects.

## Active Projects
- **SaaS / AI testing product** — AI-powered testing platform targeting mid-sized companies (his primary income-diversification goal)
- **Home server & tech projects** — self-hosted infrastructure on "burkana" (Ubuntu), Docker, Ollama, n8n, Raspberry Pi, HAB missions
- **Foosball club (roosbulls)** — community organizing, events, social energy
- **Personal learning** — Greek language, ukulele
- **Research interests** — essential oils/rose distillation, Bulgarian biotech space

## Communication Style
- Calm, grounded, and strategic — not hype, not cheerleading
- Direct and concise — no filler, no generic motivational phrases
- One sharp question at a time, never multiple
- Match Miro's language — Bulgarian or English, whichever he uses
- Treat him as a peer, not a student

## Context Injection (from n8n)
When a user message begins with a [CONTEXT] block, it contains live data pulled by the n8n workflow (calendar events, task list, last commitment, days since last check-in, etc.). Use this data naturally — do not quote it back literally, just let it inform your response.

## Behavior by Situation

**On scheduled morning check-in (trigger_type: morning_checkin):**
- Greet briefly, reference any relevant context
- Ask one focused question: what is the single most important thing to move forward today?
- Keep it under 4 sentences total

**On scheduled evening review (trigger_type: evening_review):**
- Ask what actually happened vs. what was planned
- Acknowledge the outcome (win or setback) without drama
- Suggest one micro-action to carry into tomorrow

**On weekly summary (trigger_type: weekly_summary):**
- Give a brief honest assessment of the week across all active projects
- Identify which project got neglected and ask why
- Propose one priority rebalancing decision for the coming week

**When Miro reports progress (trigger_type: progress_report):**
- Acknowledge specifically, not generically
- Connect it to the bigger picture in one sentence
- Push toward the next logical step

**When Miro reports a setback or blocker (trigger_type: setback_report):**
- Stay calm — normalize it
- Ask one diagnostic question to find the real blocker
- Offer one concrete unblocking action

**When Miro seems stuck or disengaged (trigger_type: re_anchor):**
- Do not lecture or guilt
- Ask one sharp re-anchoring question
- Remind him of his "why" in one sentence
- Offer one 30-minute task to regain momentum

**When Miro sends a free-form message (trigger_type: free_form):**
- Respond as a focused strategic partner
- Stay on topic — do not expand scope unless asked
- End with either a reflection or a next-step suggestion, not both

## Memory and Continuity
- Conversation history is stored in SQLite and injected per session
- If provided with [LAST_SESSION] summary, treat it as shared memory
- Proactively reference past commitments when relevant — do not ask what was already discussed

## Boundaries
- You are not a therapist, life coach, or general assistant
- Redirect off-topic requests gently: "That's outside my scope — want to refocus on [current project]?"
- Never moralize or repeat the same advice twice in a row
- Do not overwhelm with options — give one clear recommendation"""

# How many past messages to load as conversation history
HISTORY_WINDOW = 20

# Trigger-type system prompts injected before the user message for scheduled events
TRIGGER_PREFIXES = {
    'morning_checkin': '[TRIGGER: morning check-in — 8:30 AM]',
    'evening_review': '[TRIGGER: evening review — 9:00 PM]',
    'weekly_summary': '[TRIGGER: weekly summary — Sunday 10:00 AM]',
    're_anchor': '[TRIGGER: re-anchor — no check-in for 2+ days]',
    'progress_report': '[TRIGGER: progress report from Miro]',
    'setback_report': '[TRIGGER: setback/blocker reported by Miro]',
    'free_form': None,
}


class AIAssistantService:
    """
    Handles AI conversations for Miro's personal coach.

    Usage:
        service = AIAssistantService()
        response = service.chat(
            message="Готов съм за деня",
            session_id="telegram_chat_123",
            trigger_type="morning_checkin",
        )
    """

    def __init__(self):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it before starting the assistant."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.context_builder = ContextBuilder()

    def chat(
        self,
        message: str,
        session_id: str,
        trigger_type: str = 'free_form',
        external_context: Optional[str] = None,
    ) -> str:
        """
        Process a message, call Claude, persist history, return response.

        Args:
            message:          The user's raw message text.
            session_id:       Identifies the conversation thread (e.g. Telegram chat ID).
            trigger_type:     What triggered this message (scheduled vs. free-form).
            external_context: Optional calendar/external data injected by n8n.

        Returns:
            The assistant's response text.
        """
        # 1. Build the context block from live DB data
        context_block = self.context_builder.build_context_block(external_context)

        # 2. Construct the user content with context prefix
        trigger_prefix = TRIGGER_PREFIXES.get(trigger_type)
        parts = []
        if context_block:
            parts.append(context_block)
        if trigger_prefix:
            parts.append(trigger_prefix)
        parts.append(message)
        user_content = "\n\n".join(parts)

        # 3. Load conversation history from DB
        history = self._load_history(session_id)

        # 4. Build messages list for the API
        messages = history + [{"role": "user", "content": user_content}]

        # 5. Call Claude with streaming (prevents HTTP timeouts on long responses)
        response_text = self._call_claude(messages)

        # 6. Persist both turns (store raw message, not the context-injected version)
        self._store_message(session_id, "user", message, trigger_type)
        self._store_message(session_id, "assistant", response_text, trigger_type)

        return response_text

    def get_session_history(self, session_id: str, limit: int = 50) -> list:
        """Returns recent conversation history for a session as list of dicts."""
        with DatabaseSession() as session:
            msgs = (
                session.query(Conversation)
                .filter(Conversation.session_id == session_id)
                .order_by(Conversation.created_at.desc())
                .limit(limit)
                .all()
            )
            return [m.to_dict() for m in reversed(msgs)]

    def list_sessions(self) -> list:
        """Returns all distinct session IDs with their last activity."""
        with DatabaseSession() as db:
            from sqlalchemy import func
            rows = (
                db.query(
                    Conversation.session_id,
                    func.max(Conversation.created_at).label('last_activity'),
                    func.count(Conversation.id).label('message_count'),
                )
                .group_by(Conversation.session_id)
                .order_by(func.max(Conversation.created_at).desc())
                .all()
            )
            return [
                {
                    'session_id': r.session_id,
                    'last_activity': r.last_activity.isoformat() if r.last_activity else None,
                    'message_count': r.message_count,
                }
                for r in rows
            ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_history(self, session_id: str) -> list:
        """Load the last HISTORY_WINDOW messages as API-formatted dicts."""
        with DatabaseSession() as session:
            msgs = (
                session.query(Conversation)
                .filter(Conversation.session_id == session_id)
                .order_by(Conversation.created_at.desc())
                .limit(HISTORY_WINDOW)
                .all()
            )
            # Reverse to chronological order, format for API
            return [
                {"role": m.role, "content": m.content}
                for m in reversed(msgs)
            ]

    def _call_claude(self, messages: list) -> str:
        """Call Claude API with streaming and return the complete response text."""
        try:
            with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=1024,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                final = stream.get_final_message()

            # Extract text from response content blocks
            text_blocks = [
                block.text
                for block in final.content
                if block.type == "text"
            ]
            return "\n".join(text_blocks).strip()

        except anthropic.AuthenticationError:
            logger.error("Invalid Anthropic API key")
            raise
        except anthropic.RateLimitError:
            logger.warning("Anthropic rate limit hit")
            raise
        except anthropic.APIStatusError as e:
            logger.error("Anthropic API error %s: %s", e.status_code, e.message)
            raise

    def _store_message(
        self, session_id: str, role: str, content: str, trigger_type: str
    ) -> None:
        """Persist a single message to the conversations table."""
        with DatabaseSession() as session:
            msg = Conversation(
                session_id=session_id,
                role=role,
                content=content,
                trigger_type=trigger_type,
            )
            session.add(msg)
