"""
Association tables for many-to-many relationships
"""

from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime, Text
from datetime import datetime
from leadsauce.utils.db import Base

# Profile-Tag association
profile_tags = Table(
    'profile_tags',
    Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

# Relationships between profiles
relationships = Table(
    'relationships',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('from_profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
    Column('to_profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
    Column('relation_type', String(100), nullable=False),
    Column('note', Text),
    Column('created_at', DateTime, default=datetime.utcnow)
)
