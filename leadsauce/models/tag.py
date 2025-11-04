"""
Tag model for organizing contacts
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base
from leadsauce.models.associations import profile_tags


class Tag(Base):
    """Tag model for organizing and categorizing profiles"""

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Tag details
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7))  # Hex color code (e.g., #FF5733)
    description = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profiles = relationship('Profile', secondary=profile_tags, back_populates='tags')

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"

    def to_dict(self, include_count=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_count:
            data['profile_count'] = len(self.profiles)

        return data
