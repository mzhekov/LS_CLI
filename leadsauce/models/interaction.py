"""
Interaction model for logging communications
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class Interaction(Base):
    """Interaction model for logging communications with contacts"""

    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Interaction details
    interaction_type = Column(String(50), nullable=False, index=True)  # meeting, call, email, note, event
    subject = Column(String(255))
    notes = Column(Text)
    interaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Visibility
    visibility = Column(String(50), default='private')  # private, team, shared

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship('Profile', back_populates='interactions')
    user = relationship('User', back_populates='interactions')

    def __repr__(self):
        return f"<Interaction(id={self.id}, type='{self.interaction_type}', profile_id={self.profile_id})>"

    def to_dict(self, include_profile=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'profile_id': self.profile_id,
            'user_id': self.user_id,
            'interaction_type': self.interaction_type,
            'subject': self.subject,
            'notes': self.notes,
            'interaction_date': self.interaction_date.isoformat() if self.interaction_date else None,
            'visibility': self.visibility,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_profile and self.profile:
            data['profile'] = {
                'id': self.profile.id,
                'name': self.profile.name,
                'email': self.profile.email
            }

        return data
