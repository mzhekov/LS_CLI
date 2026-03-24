"""
Unit tests for ProfileRelationship and CompanyRelationship models — all CRUD and every attribute
"""

import pytest
from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company

PROFILE_RELATIONSHIP_TYPES = [
    "Reports To", "Manages", "Mentor", "Mentee", "Friend",
    "Colleague", "Business Partner", "Client", "Vendor Contact",
    "Advisor", "Competitor", "Other"
]
COMPANY_RELATIONSHIP_TYPES = [
    "Partner", "Client", "Supplier", "Vendor", "Competitor",
    "Parent Company", "Subsidiary", "Investor", "Investee",
    "Affiliate", "Strategic Alliance", "Other"
]
RELATIONSHIP_STATUSES = ["Good", "Bad", "No Interest"]


# ============================================================================
# PROFILE RELATIONSHIP TESTS
# ============================================================================

class TestProfileRelationshipCreate:

    def test_create_minimal(self, test_db, sample_profiles):
        rel = ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[1].id,
            relationship_type="Colleague"
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.id is not None
        assert rel.from_profile_id == sample_profiles[0].id
        assert rel.to_profile_id == sample_profiles[1].id
        assert rel.relationship_type == "Colleague"
        assert rel.status == "Good"
        assert rel.bidirectional is False
        assert rel.description is None
        assert rel.created_at is not None

    def test_create_all_fields(self, test_db, sample_profiles):
        rel = ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[1].id,
            relationship_type="Mentor",
            description="John mentors Jane on leadership skills",
            status="Good",
            bidirectional=False
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.relationship_type == "Mentor"
        assert rel.description == "John mentors Jane on leadership skills"
        assert rel.status == "Good"
        assert rel.bidirectional is False

    def test_create_bidirectional(self, test_db, sample_profiles):
        rel = ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[1].id,
            relationship_type="Friend",
            bidirectional=True
        )
        test_db.add(rel)
        test_db.commit()
        assert rel.bidirectional is True

    def test_create_all_relationship_types(self, test_db, sample_profiles):
        for i, rel_type in enumerate(PROFILE_RELATIONSHIP_TYPES):
            rel = ProfileRelationship(
                from_profile_id=sample_profiles[0].id,
                to_profile_id=sample_profiles[(i % 3) + 1].id,
                relationship_type=rel_type
            )
            test_db.add(rel)
        test_db.commit()
        stored = [r.relationship_type for r in test_db.query(ProfileRelationship).all()]
        for rel_type in PROFILE_RELATIONSHIP_TYPES:
            assert rel_type in stored

    def test_create_all_statuses(self, test_db, sample_profiles):
        for i, status in enumerate(RELATIONSHIP_STATUSES):
            rel = ProfileRelationship(
                from_profile_id=sample_profiles[0].id,
                to_profile_id=sample_profiles[(i % 3) + 1].id,
                relationship_type="Other",
                status=status
            )
            test_db.add(rel)
        test_db.commit()
        stored = [r.status for r in test_db.query(ProfileRelationship).all()]
        for status in RELATIONSHIP_STATUSES:
            assert status in stored


class TestProfileRelationshipRead:

    def test_read_by_id(self, test_db, sample_profile_relationships):
        r = test_db.query(ProfileRelationship).filter_by(id=sample_profile_relationships[0].id).first()
        assert r is not None

    def test_read_all(self, test_db, sample_profile_relationships):
        assert test_db.query(ProfileRelationship).count() == 4

    def test_read_by_from_profile(self, test_db, sample_profile_relationships, sample_profiles):
        rels = test_db.query(ProfileRelationship).filter_by(from_profile_id=sample_profiles[0].id).all()
        assert len(rels) == 2

    def test_read_by_type(self, test_db, sample_profile_relationships):
        assert test_db.query(ProfileRelationship).filter_by(relationship_type="Friend").count() == 1

    def test_read_bidirectional(self, test_db, sample_profile_relationships):
        assert test_db.query(ProfileRelationship).filter_by(bidirectional=True).count() == 2

    def test_read_by_status_good(self, test_db, sample_profile_relationships):
        assert test_db.query(ProfileRelationship).filter_by(status="Good").count() == 3

    def test_read_by_status_no_interest(self, test_db, sample_profile_relationships):
        assert test_db.query(ProfileRelationship).filter_by(status="No Interest").count() == 1

    def test_read_profile_backlinks(self, test_db, sample_profile_relationships, sample_profiles):
        rel = test_db.query(ProfileRelationship).filter_by(relationship_type="Colleague").first()
        assert rel.from_profile.name == sample_profiles[0].name
        assert rel.to_profile.name == sample_profiles[1].name


class TestProfileRelationshipUpdate:

    def test_update_type(self, test_db, sample_profile_relationships):
        r = sample_profile_relationships[0]
        r.relationship_type = "Business Partner"
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(id=r.id).first().relationship_type == "Business Partner"

    def test_update_status_to_bad(self, test_db, sample_profile_relationships):
        r = sample_profile_relationships[0]
        r.status = "Bad"
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(id=r.id).first().status == "Bad"

    def test_update_bidirectional_flag(self, test_db, sample_profile_relationships):
        r = sample_profile_relationships[1]
        r.bidirectional = True
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(id=r.id).first().bidirectional is True

    def test_update_description(self, test_db, sample_profile_relationships):
        r = sample_profile_relationships[0]
        r.description = "Updated after reconnecting"
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(id=r.id).first().description == "Updated after reconnecting"

    def test_update_status_to_no_interest(self, test_db, sample_profile_relationships):
        r = sample_profile_relationships[2]
        r.status = "No Interest"
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(id=r.id).first().status == "No Interest"


class TestProfileRelationshipDelete:

    def test_delete_relationship(self, test_db, sample_profile_relationships):
        rid = sample_profile_relationships[0].id
        test_db.delete(sample_profile_relationships[0])
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(id=rid).first() is None

    def test_delete_preserves_profiles(self, test_db, sample_profile_relationships, sample_profiles):
        r = sample_profile_relationships[0]
        from_id, to_id = r.from_profile_id, r.to_profile_id
        test_db.delete(r)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=from_id).first() is not None
        assert test_db.query(Profile).filter_by(id=to_id).first() is not None

    def test_deleting_profile_cascades_relationships(self, test_db, sample_profile_relationships, sample_profiles):
        pid = sample_profiles[0].id
        test_db.delete(sample_profiles[0])
        test_db.commit()
        remaining = test_db.query(ProfileRelationship).filter(
            (ProfileRelationship.from_profile_id == pid) |
            (ProfileRelationship.to_profile_id == pid)
        ).all()
        assert len(remaining) == 0


class TestProfileRelationshipNetworkQueries:

    def test_all_connections_for_profile(self, test_db, sample_profile_relationships, sample_profiles):
        pid = sample_profiles[0].id
        connections = test_db.query(ProfileRelationship).filter(
            (ProfileRelationship.from_profile_id == pid) |
            (ProfileRelationship.to_profile_id == pid)
        ).all()
        assert len(connections) >= 2

    def test_status_summary(self, test_db, sample_profile_relationships):
        from sqlalchemy import func
        statuses = dict(test_db.query(
            ProfileRelationship.status, func.count(ProfileRelationship.id)
        ).group_by(ProfileRelationship.status).all())
        assert statuses.get("Good", 0) == 3

    def test_to_dict(self, test_db, sample_profile_relationships):
        d = sample_profile_relationships[0].to_dict()
        assert 'relationship_type' in d
        assert 'status' in d
        assert 'bidirectional' in d


# ============================================================================
# COMPANY RELATIONSHIP TESTS
# ============================================================================

class TestCompanyRelationshipCreate:

    def test_create_minimal(self, test_db, sample_companies):
        rel = CompanyRelationship(
            from_company_id=sample_companies[0].id,
            to_company_id=sample_companies[1].id,
            relationship_type="Partner"
        )
        test_db.add(rel)
        test_db.commit()

        assert rel.id is not None
        assert rel.relationship_type == "Partner"
        assert rel.status == "Good"
        assert rel.bidirectional is False
        assert rel.description is None

    def test_create_all_fields(self, test_db, sample_companies):
        rel = CompanyRelationship(
            from_company_id=sample_companies[0].id,
            to_company_id=sample_companies[1].id,
            relationship_type="Supplier",
            description="Hardware supply since 2020",
            status="Good",
            bidirectional=True
        )
        test_db.add(rel)
        test_db.commit()
        assert rel.description == "Hardware supply since 2020"
        assert rel.bidirectional is True

    def test_create_all_relationship_types(self, test_db, sample_companies):
        for rel_type in COMPANY_RELATIONSHIP_TYPES:
            rel = CompanyRelationship(
                from_company_id=sample_companies[0].id,
                to_company_id=sample_companies[1].id,
                relationship_type=rel_type
            )
            test_db.add(rel)
        test_db.commit()
        stored = [r.relationship_type for r in test_db.query(CompanyRelationship).all()]
        for rel_type in COMPANY_RELATIONSHIP_TYPES:
            assert rel_type in stored

    def test_create_all_statuses(self, test_db, sample_companies):
        for status in RELATIONSHIP_STATUSES:
            rel = CompanyRelationship(
                from_company_id=sample_companies[0].id,
                to_company_id=sample_companies[1].id,
                relationship_type="Other",
                status=status
            )
            test_db.add(rel)
        test_db.commit()
        stored = [r.status for r in test_db.query(CompanyRelationship).all()]
        for status in RELATIONSHIP_STATUSES:
            assert status in stored


class TestCompanyRelationshipRead:

    def test_read_all(self, test_db, sample_company_relationships):
        assert test_db.query(CompanyRelationship).count() == 3

    def test_read_by_from_company(self, test_db, sample_company_relationships, sample_companies):
        rels = test_db.query(CompanyRelationship).filter_by(from_company_id=sample_companies[0].id).all()
        assert len(rels) == 2

    def test_read_by_type(self, test_db, sample_company_relationships):
        assert test_db.query(CompanyRelationship).filter_by(relationship_type="Partner").count() == 1

    def test_read_bidirectional(self, test_db, sample_company_relationships):
        assert test_db.query(CompanyRelationship).filter_by(bidirectional=True).count() == 2

    def test_read_bad_status(self, test_db, sample_company_relationships):
        bad = test_db.query(CompanyRelationship).filter_by(status="Bad").all()
        assert len(bad) == 1
        assert bad[0].relationship_type == "Competitor"

    def test_read_company_backlinks(self, test_db, sample_company_relationships, sample_companies):
        rel = test_db.query(CompanyRelationship).filter_by(relationship_type="Partner").first()
        assert rel.from_company.name == sample_companies[0].name


class TestCompanyRelationshipUpdate:

    def test_update_type(self, test_db, sample_company_relationships):
        r = sample_company_relationships[0]
        r.relationship_type = "Strategic Alliance"
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(id=r.id).first().relationship_type == "Strategic Alliance"

    def test_update_status(self, test_db, sample_company_relationships):
        r = sample_company_relationships[0]
        r.status = "Bad"
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(id=r.id).first().status == "Bad"

    def test_update_bidirectional(self, test_db, sample_company_relationships):
        r = sample_company_relationships[1]
        r.bidirectional = True
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(id=r.id).first().bidirectional is True

    def test_update_description(self, test_db, sample_company_relationships):
        r = sample_company_relationships[0]
        r.description = "Renewed 2024"
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(id=r.id).first().description == "Renewed 2024"


class TestCompanyRelationshipDelete:

    def test_delete(self, test_db, sample_company_relationships):
        rid = sample_company_relationships[0].id
        test_db.delete(sample_company_relationships[0])
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(id=rid).first() is None

    def test_delete_preserves_companies(self, test_db, sample_company_relationships, sample_companies):
        r = sample_company_relationships[0]
        from_id, to_id = r.from_company_id, r.to_company_id
        test_db.delete(r)
        test_db.commit()
        assert test_db.query(Company).filter_by(id=from_id).first() is not None
        assert test_db.query(Company).filter_by(id=to_id).first() is not None

    def test_deleting_company_cascades_relationships(self, test_db, sample_company_relationships, sample_companies):
        cid = sample_companies[0].id
        test_db.delete(sample_companies[0])
        test_db.commit()
        remaining = test_db.query(CompanyRelationship).filter(
            (CompanyRelationship.from_company_id == cid) |
            (CompanyRelationship.to_company_id == cid)
        ).all()
        assert len(remaining) == 0

    def test_to_dict(self, test_db, sample_company_relationships):
        d = sample_company_relationships[0].to_dict()
        assert 'relationship_type' in d
        assert 'status' in d
        assert 'bidirectional' in d
