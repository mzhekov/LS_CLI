"""
Team and TeamMember models for collaboration
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class Team(Base):
    """Team model for collaboration"""

    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship('TeamMember', back_populates='team', cascade='all, delete-orphan')
    profiles = relationship('Profile', back_populates='team')
    companies = relationship('Company', back_populates='team')

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

    def to_dict(self, include_members=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'member_count': len(self.members),
            'profile_count': len(self.profiles),
            'company_count': len(self.companies)
        }

        if include_members:
            data['members'] = [m.to_dict() for m in self.members]

        return data


class TeamMember(Base):
    """TeamMember model for team membership"""

    __tablename__ = 'team_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)

    # Member details
    name = Column(String(255))
    email = Column(String(255), index=True)

    # Role
    role = Column(String(50), default='member', index=True)  # owner, admin, editor, viewer, member

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    team = relationship('Team', back_populates='members')

    # Constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'email', name='unique_team_member'),
    )

    def __repr__(self):
        return f"<TeamMember(id={self.id}, team_id={self.team_id}, email='{self.email}', role='{self.role}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }
