"""
Document model for file management
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class Document(Base):
    """Document model for managing files attached to profiles"""

    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_document_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))

    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_type = Column(String(100))  # MIME type

    # Document metadata
    document_type = Column(String(50))  # resume, contract, presentation, etc.
    description = Column(Text)
    folder = Column(String(255))  # Virtual folder for organization

    # Version control
    version = Column(Integer, default=1)
    is_latest_version = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship('Profile', back_populates='documents')
    parent_document = relationship('Document', remote_side=[id], backref='versions')

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', profile_id={self.profile_id})>"

    def to_dict(self, include_profile=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'profile_id': self.profile_id,
            
            'parent_document_id': self.parent_document_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'document_type': self.document_type,
            'description': self.description,
            'folder': self.folder,
            'version': self.version,
            'is_latest_version': self.is_latest_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_profile and self.profile:
            data['profile'] = {
                'id': self.profile.id,
                'name': self.profile.name
            }

        return data
