"""
User model
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class User(Base):
    """User model"""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Subscription info
    subscription_tier = Column(String(50), default='free')
    subscription_status = Column(String(50), default='active')

    # Profile info
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    profiles = relationship('Profile', foreign_keys='Profile.user_id', back_populates='user', cascade='all, delete-orphan')
    companies = relationship('Company', back_populates='user', cascade='all, delete-orphan')
    tags = relationship('Tag', back_populates='user', cascade='all, delete-orphan')
    interactions = relationship('Interaction', back_populates='user', cascade='all, delete-orphan')
    reminders = relationship('Reminder', back_populates='user', cascade='all, delete-orphan')
    created_teams = relationship('Team', foreign_keys='Team.created_by_id', back_populates='creator')
    team_memberships = relationship('TeamMember', foreign_keys='TeamMember.user_id', back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
