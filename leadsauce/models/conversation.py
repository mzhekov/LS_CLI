"""
Conversation history model for AI assistant sessions.
Each row is one message (user or assistant) in a session.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from leadsauce.utils.db import Base


class Conversation(Base):
    """Stores AI assistant conversation history per session (e.g. Telegram chat ID)."""

    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identifies the conversation thread (e.g. Telegram chat ID)
    session_id = Column(String(100), nullable=False, index=True)

    # 'user' or 'assistant'
    role = Column(String(20), nullable=False)

    # The message content (raw, without injected context)
    content = Column(Text, nullable=False)

    # What triggered this exchange — used to tune AI behavior
    # morning_checkin | evening_review | weekly_summary |
    # re_anchor | free_form | progress_report | setback_report
    trigger_type = Column(String(50), default='free_form')

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        preview = self.content[:40].replace('\n', ' ')
        return f"<Conversation(session={self.session_id}, role={self.role}, '{preview}...')>"

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'trigger_type': self.trigger_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
