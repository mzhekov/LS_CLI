"""
Company model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class Company(Base):
    """Company model"""

    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='SET NULL'), index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100))
    size = Column(String(50))
    location = Column(String(255))
    website = Column(String(255))
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='companies')
    team = relationship('Team', back_populates='companies')
    profiles = relationship('Profile', back_populates='company')

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"

    def to_dict(self, include_profiles=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'name': self.name,
            'industry': self.industry,
            'size': self.size,
            'location': self.location,
            'website': self.website,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_profiles:
            data['profiles'] = [p.to_dict() for p in self.profiles]
            data['profile_count'] = len(self.profiles)

        return data
