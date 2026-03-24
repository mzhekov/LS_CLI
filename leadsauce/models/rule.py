"""
Rule model — user-defined instructions that are injected into the AI assistant's
system prompt, similar to Claude's "Custom Instructions" feature.

Rules can be scoped to specific trigger types (morning_checkin, evening_review,
weekly_summary, re_anchor, progress_report, setback_report, free_form) or set
to 'always' to apply to every conversation.

Examples of useful rules:
  - "Always respond in Bulgarian"
  - "Never suggest more than one task at a time"
  - "When I mention roosbulls always ask about the next event"
  - "During evening_review, always ask about energy level, not just task output"
  - "If I haven't made progress on the SaaS goal in a week, call it out directly"
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from leadsauce.utils.db import Base

# Valid trigger types (plus 'always')
VALID_SCOPES = {
    'always',
    'morning_checkin',
    'evening_review',
    'weekly_summary',
    're_anchor',
    'progress_report',
    'setback_report',
    'free_form',
}


class Rule(Base):
    """A user-defined instruction that shapes the AI assistant's behavior."""

    __tablename__ = 'rules'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Short label shown in listings (e.g. "Language preference")
    title = Column(String(200), nullable=False)

    # The actual instruction text injected into the system prompt
    content = Column(Text, nullable=False)

    # When this rule applies:
    #   'always'         — every conversation, every trigger
    #   '<trigger_type>' — only when that trigger fires (e.g. 'morning_checkin')
    #   Comma-separated  — multiple specific triggers (e.g. 'morning_checkin,evening_review')
    scope = Column(String(200), nullable=False, default='always', index=True)

    # Rules are applied in ascending priority order (lower number = earlier in prompt)
    priority = Column(Integer, nullable=False, default=50)

    # Soft toggle — disable without deleting
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Rule(id={self.id}, title='{self.title}', scope='{self.scope}', active={self.is_active})>"

    def applies_to(self, trigger_type: str) -> bool:
        """Return True if this rule should apply for the given trigger_type."""
        if not self.is_active:
            return False
        scopes = [s.strip() for s in self.scope.split(',')]
        return 'always' in scopes or trigger_type in scopes

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'scope': self.scope,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
