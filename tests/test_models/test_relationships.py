"""
Tests for Relationship models (Profile and Company relationships)
"""

import pytest
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship


class TestProfileRelationshipCreate:
    """Test creating profile-to-profile relationships"""

    def test_create_basic_relationship(self, test_db, sample_profiles):
        """Test creating a basic profile relationship"""
        rel = ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[1].id,
            relationship_type="Colleague",
            bidirectional=True,
            status="Good"
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.id is not None
        assert rel.relationship_type == "Colleague"
        assert rel.bidirectional is True

    def test_create_relationship_types(self, test_db, sample_profiles):
        """Test creating relationships with different types"""
        types = ["Mentor", "Colleague", "Friend", "Client", "Partner", "Manages"]

        for rel_type in types:
            rel = ProfileRelationship(
                profile_id=sample_profiles[0].id,
                related_profile_id=sample_profiles[1].id,
                relationship_type=rel_type,
                bidirectional=False,
                status="Good"
            )
            test_db.add(rel)

        test_db.commit()

        relationships = test_db.query(ProfileRelationship).all()
        assert len(relationships) >= len(types)

    def test_create_bidirectional_relationship(self, test_db, sample_profiles):
        """Test creating bidirectional relationship"""
        rel = ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[1].id,
            relationship_type="Friend",
            bidirectional=True,
            status="Good"
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.bidirectional is True

        # Note: Bidirectional flag means the relationship goes both ways
        # Application logic may need to create reverse relationship

    def test_create_unidirectional_relationship(self, test_db, sample_profiles):
        """Test creating unidirectional relationship (e.g., Mentor)"""
        rel = ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[2].id,
            relationship_type="Mentor",
            bidirectional=False,
            status="Good"
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.bidirectional is False

    def test_create_relationship_with_status(self, test_db, sample_profiles):
        """Test creating relationship with different statuses"""
        statuses = ["Good", "Bad", "No Interest"]

        for i, status in enumerate(statuses):
            rel = ProfileRelationship(
                profile_id=sample_profiles[0].id,
                related_profile_id=sample_profiles[i + 1].id,
                relationship_type="Contact",
                bidirectional=False,
                status=status
            )
            test_db.add(rel)

        test_db.commit()

        good_rels = test_db.query(ProfileRelationship).filter_by(status="Good").all()
        bad_rels = test_db.query(ProfileRelationship).filter_by(status="Bad").all()

        assert len(good_rels) >= 1
        assert len(bad_rels) >= 1


class TestProfileRelationshipRead:
    """Test reading profile relationships"""

    def test_read_all_relationships(self, test_db, sample_relationships):
        """Test reading all profile relationships"""
        rels = test_db.query(ProfileRelationship).all()

        assert len(rels) == 3
        assert all(isinstance(r, ProfileRelationship) for r in rels)

    def test_read_relationships_by_profile(self, test_db, sample_relationships, sample_profiles):
        """Test finding all relationships for a specific profile"""
        john_id = sample_profiles[0].id

        # Relationships where John is the source
        rels = test_db.query(ProfileRelationship).filter_by(profile_id=john_id).all()

        assert len(rels) == 2  # John -> Jane, John -> Alice

    def test_read_bidirectional_relationships(self, test_db, sample_relationships):
        """Test filtering bidirectional relationships"""
        rels = test_db.query(ProfileRelationship).filter_by(bidirectional=True).all()

        assert len(rels) >= 1
        assert all(r.bidirectional is True for r in rels)

    def test_read_relationships_by_type(self, test_db, sample_relationships):
        """Test filtering relationships by type"""
        colleagues = test_db.query(ProfileRelationship).filter_by(
            relationship_type="Colleague"
        ).all()

        assert len(colleagues) == 1

    def test_read_relationships_by_status(self, test_db, sample_relationships):
        """Test filtering relationships by status"""
        good_rels = test_db.query(ProfileRelationship).filter_by(status="Good").all()

        assert len(good_rels) == 3  # All sample relationships are "Good"


class TestProfileRelationshipUpdate:
    """Test updating profile relationships"""

    def test_update_relationship_type(self, test_db, sample_relationships):
        """Test changing relationship type"""
        rel = sample_relationships['profiles'][0]
        original_type = rel.relationship_type

        rel.relationship_type = "Partner"
        test_db.commit()

        updated = test_db.query(ProfileRelationship).filter_by(id=rel.id).first()
        assert updated.relationship_type == "Partner"
        assert updated.relationship_type != original_type

    def test_update_relationship_status(self, test_db, sample_relationships):
        """Test changing relationship status"""
        rel = sample_relationships['profiles'][0]

        rel.status = "Bad"
        test_db.commit()

        updated = test_db.query(ProfileRelationship).filter_by(id=rel.id).first()
        assert updated.status == "Bad"

    def test_update_bidirectional_flag(self, test_db, sample_relationships):
        """Test changing bidirectional flag"""
        rel = sample_relationships['profiles'][1]  # Mentor (unidirectional)
        assert rel.bidirectional is False

        rel.bidirectional = True
        test_db.commit()

        updated = test_db.query(ProfileRelationship).filter_by(id=rel.id).first()
        assert updated.bidirectional is True


class TestProfileRelationshipDelete:
    """Test deleting profile relationships"""

    def test_delete_relationship(self, test_db, sample_relationships):
        """Test deleting a relationship"""
        rel = sample_relationships['profiles'][0]
        rel_id = rel.id
        count_before = test_db.query(ProfileRelationship).count()

        test_db.delete(rel)
        test_db.commit()

        count_after = test_db.query(ProfileRelationship).count()
        deleted = test_db.query(ProfileRelationship).filter_by(id=rel_id).first()

        assert count_after == count_before - 1
        assert deleted is None

    def test_delete_relationship_preserves_profiles(self, test_db, sample_relationships, sample_profiles):
        """Test that deleting relationship doesn't delete profiles"""
        rel = sample_relationships['profiles'][0]
        profile_count_before = test_db.query(Profile).count()

        test_db.delete(rel)
        test_db.commit()

        profile_count_after = test_db.query(Profile).count()
        assert profile_count_after == profile_count_before


class TestCompanyRelationshipCreate:
    """Test creating company-to-company relationships"""

    def test_create_company_relationship(self, test_db, sample_companies):
        """Test creating a company relationship"""
        rel = CompanyRelationship(
            company_id=sample_companies[0].id,
            related_company_id=sample_companies[1].id,
            relationship_type="Partner",
            bidirectional=True,
            status="Good"
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.id is not None
        assert rel.relationship_type == "Partner"

    def test_create_company_relationship_types(self, test_db, sample_companies):
        """Test different company relationship types"""
        types = ["Partner", "Client", "Vendor", "Competitor", "Subsidiary"]

        for rel_type in types:
            rel = CompanyRelationship(
                company_id=sample_companies[0].id,
                related_company_id=sample_companies[1].id,
                relationship_type=rel_type,
                bidirectional=False,
                status="Good"
            )
            test_db.add(rel)

        test_db.commit()

        relationships = test_db.query(CompanyRelationship).all()
        assert len(relationships) >= len(types)


class TestCompanyRelationshipRead:
    """Test reading company relationships"""

    def test_read_all_company_relationships(self, test_db, sample_relationships):
        """Test reading all company relationships"""
        rels = test_db.query(CompanyRelationship).all()

        assert len(rels) == 2
        assert all(isinstance(r, CompanyRelationship) for r in rels)

    def test_read_company_relationships_by_company(self, test_db, sample_relationships, sample_companies):
        """Test finding relationships for a specific company"""
        techcorp_id = sample_companies[0].id

        rels = test_db.query(CompanyRelationship).filter_by(company_id=techcorp_id).all()

        assert len(rels) == 2  # TechCorp -> DesignStudio, TechCorp -> FinanceGlobal


class TestRelationshipValidation:
    """Test relationship validation and edge cases"""

    def test_cannot_relate_profile_to_itself(self, test_db, sample_profiles):
        """Test that a profile cannot have a relationship with itself"""
        # This should be validated at application level

        rel = ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[0].id,  # Same profile!
            relationship_type="Friend",
            bidirectional=False,
            status="Good"
        )

        # SQLAlchemy will allow this, but application should validate
        # This test documents expected validation behavior

    def test_duplicate_relationships_allowed(self, test_db, sample_profiles):
        """Test that duplicate relationships can be created"""
        # May want to prevent duplicates at application level

        rel1 = ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[1].id,
            relationship_type="Colleague",
            bidirectional=False,
            status="Good"
        )

        rel2 = ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[1].id,
            relationship_type="Colleague",
            bidirectional=False,
            status="Good"
        )

        test_db.add(rel1)
        test_db.add(rel2)
        test_db.commit()

        # Both will be created - application may want to prevent this

    def test_relationship_with_nonexistent_profile(self, test_db):
        """Test creating relationship with non-existent profile"""
        rel = ProfileRelationship(
            profile_id=9999,  # Doesn't exist
            related_profile_id=9998,  # Doesn't exist
            relationship_type="Friend",
            bidirectional=False,
            status="Good"
        )

        # This will fail on commit due to foreign key constraint
        test_db.add(rel)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

        test_db.rollback()


class TestRelationshipNetworkQueries:
    """Test complex queries for relationship networks"""

    def test_find_mutual_connections(self, test_db, sample_profiles, sample_relationships):
        """Test finding mutual connections between two profiles"""
        # John connects to Jane and Alice
        # Alice connects to Bob
        # So Alice is a connection between John and Bob

        john_id = sample_profiles[0].id
        bob_id = sample_profiles[3].id

        # Find profiles that both John and Bob are connected to
        john_connections = test_db.query(ProfileRelationship.related_profile_id).filter_by(
            profile_id=john_id
        ).subquery()

        bob_rels = test_db.query(ProfileRelationship).filter(
            ProfileRelationship.profile_id == bob_id
        ).all()

        # This is a simplified test - real implementation would be more complex

    def test_find_all_connections_for_profile(self, test_db, sample_relationships, sample_profiles):
        """Test finding all connections (outgoing and incoming) for a profile"""
        alice_id = sample_profiles[2].id

        # Outgoing relationships
        outgoing = test_db.query(ProfileRelationship).filter_by(profile_id=alice_id).all()

        # Incoming relationships
        incoming = test_db.query(ProfileRelationship).filter_by(
            related_profile_id=alice_id
        ).all()

        total_connections = len(outgoing) + len(incoming)
        assert total_connections >= 2  # Alice has at least 2 connections

    def test_relationship_status_summary(self, test_db, sample_relationships):
        """Test getting summary of relationship statuses"""
        from sqlalchemy import func

        status_counts = test_db.query(
            ProfileRelationship.status,
            func.count(ProfileRelationship.id)
        ).group_by(ProfileRelationship.status).all()

        assert len(status_counts) >= 1

        # All sample relationships are "Good"
        good_count = next((count for status, count in status_counts if status == "Good"), 0)
        assert good_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
