"""
Profile model for contacts
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base
from leadsauce.models.associations import profile_tags


class Profile(Base):
    """Profile model for professional contacts"""

    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='SET NULL'), index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='SET NULL'), index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(50))

    # Professional info
    seniority = Column(String(50), nullable=False, index=True)
    generation = Column(String(50))
    married = Column(Boolean, default=False)
    has_children = Column(Boolean, default=False)

    # Personality traits (MBTI-style scores)
    ie_score = Column(Integer)  # Introvert (0) to Extrovert (100)
    is_score = Column(Integer)  # Intuitive (0) to Sensing (100)

    # Skills and interests
    good_at = Column(Text)  # What they're good at (skills)
    need_to_work = Column(Text)  # Areas for improvement
    work_for = Column(Text)  # What motivates them / what they work for

    # Additional information
    additional_info = Column(Text)
    notes = Column(Text)

    # Activity tracking
    last_contact = Column(DateTime, index=True)
    interaction_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship('Company', back_populates='profiles')
    team = relationship('Team', back_populates='profiles')
    interactions = relationship('Interaction', back_populates='profile', cascade='all, delete-orphan', order_by='Interaction.interaction_date.desc()')
    reminders = relationship('Reminder', back_populates='profile', cascade='all, delete-orphan', order_by='Reminder.reminder_date.asc()')
    documents = relationship('Document', back_populates='profile', cascade='all, delete-orphan')
    tags = relationship('Tag', secondary=profile_tags, back_populates='profiles')

    def __repr__(self):
        return f"<Profile(id={self.id}, name='{self.name}')>"

    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'team_id': self.team_id,
            'company_id': self.company_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'seniority': self.seniority,
            'generation': self.generation,
            'married': self.married,
            'has_children': self.has_children,
            'ie_score': self.ie_score,
            'is_score': self.is_score,
            'good_at': self.good_at,
            'need_to_work': self.need_to_work,
            'work_for': self.work_for,
            'additional_info': self.additional_info,
            'notes': self.notes,
            'last_contact': self.last_contact.isoformat() if self.last_contact else None,
            'interaction_count': self.interaction_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_relations:
            data['company'] = self.company.to_dict() if self.company else None
            data['tags'] = [tag.to_dict() for tag in self.tags]
            data['interaction_count_actual'] = len(self.interactions)
            data['reminder_count'] = len([r for r in self.reminders if not r.completed])
            data['document_count'] = len(self.documents)

        return data

    def update_last_contact(self):
        """Update last contact timestamp"""
        self.last_contact = datetime.utcnow()
        self.interaction_count = len(self.interactions)
