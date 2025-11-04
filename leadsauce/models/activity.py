"""
Activity model for tracking user actions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class Activity(Base):
    """Activity model for tracking user actions and audit trail"""

    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, index=True)

    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)  # create, update, delete, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # profile, company, interaction, etc.
    entity_id = Column(Integer, index=True)
    description = Column(Text)

    # Additional metadata
    activity_metadata = Column(JSON)  # Store additional info as JSON

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    team = relationship('Team')

    def __repr__(self):
        return f"<Activity(id={self.id}, type='{self.activity_type}', entity='{self.entity_type}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            
            'team_id': self.team_id,
            'activity_type': self.activity_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'metadata': self.activity_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            
        }
