"""
Relationship model for mapping connections between profiles and companies
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class ProfileRelationship(Base):
    """Relationship between two profiles (person to person)"""

    __tablename__ = 'profile_relationships'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Source and target profiles
    from_profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    to_profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)

    # Relationship details
    relationship_type = Column(String(100), nullable=False)  # e.g., "reports to", "mentor", "friend", "colleague"
    description = Column(Text)

    # Is this bidirectional? (e.g., "friends" is bidirectional, "reports to" is not)
    bidirectional = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_profile = relationship('Profile', foreign_keys=[from_profile_id], backref='relationships_from')
    to_profile = relationship('Profile', foreign_keys=[to_profile_id], backref='relationships_to')

    def __repr__(self):
        return f"<ProfileRelationship(from={self.from_profile_id}, to={self.to_profile_id}, type='{self.relationship_type}')>"

    def to_dict(self, include_profiles=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'from_profile_id': self.from_profile_id,
            'to_profile_id': self.to_profile_id,
            'relationship_type': self.relationship_type,
            'description': self.description,
            'bidirectional': self.bidirectional,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_profiles:
            if self.from_profile:
                data['from_profile'] = {
                    'id': self.from_profile.id,
                    'name': self.from_profile.name
                }
            if self.to_profile:
                data['to_profile'] = {
                    'id': self.to_profile.id,
                    'name': self.to_profile.name
                }

        return data


class CompanyRelationship(Base):
    """Relationship between two companies (organization to organization)"""

    __tablename__ = 'company_relationships'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Source and target companies
    from_company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    to_company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)

    # Relationship details
    relationship_type = Column(String(100), nullable=False)  # e.g., "partner", "supplier", "client", "competitor", "parent company"
    description = Column(Text)

    # Is this bidirectional? (e.g., "partners" is bidirectional, "supplier" might not be)
    bidirectional = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_company = relationship('Company', foreign_keys=[from_company_id], backref='relationships_from')
    to_company = relationship('Company', foreign_keys=[to_company_id], backref='relationships_to')

    def __repr__(self):
        return f"<CompanyRelationship(from={self.from_company_id}, to={self.to_company_id}, type='{self.relationship_type}')>"

    def to_dict(self, include_companies=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'from_company_id': self.from_company_id,
            'to_company_id': self.to_company_id,
            'relationship_type': self.relationship_type,
            'description': self.description,
            'bidirectional': self.bidirectional,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_companies:
            if self.from_company:
                data['from_company'] = {
                    'id': self.from_company.id,
                    'name': self.from_company.name
                }
            if self.to_company:
                data['to_company'] = {
                    'id': self.to_company.id,
                    'name': self.to_company.name
                }

        return data


# Common relationship types for profiles
PROFILE_RELATIONSHIP_TYPES = [
    "Reports To",
    "Manages",
    "Mentor",
    "Mentee",
    "Friend",
    "Colleague",
    "Business Partner",
    "Client",
    "Vendor Contact",
    "Advisor",
    "Competitor",
    "Other"
]

# Common relationship types for companies
COMPANY_RELATIONSHIP_TYPES = [
    "Partner",
    "Client",
    "Supplier",
    "Vendor",
    "Competitor",
    "Parent Company",
    "Subsidiary",
    "Investor",
    "Investee",
    "Affiliate",
    "Strategic Alliance",
    "Other"
]
