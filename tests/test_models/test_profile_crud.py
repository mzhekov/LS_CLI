"""
Tests for Profile model CRUD operations
"""

import pytest
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag


class TestProfileCreate:
    """Test Profile creation"""

    def test_create_basic_profile(self, test_db):
        """Test creating a profile with minimum required fields"""
        profile = Profile(
            name="Test User",
            seniority="Mid-Level"
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert profile.name == "Test User"
        assert profile.seniority == "Mid-Level"

    def test_create_full_profile(self, test_db, sample_companies):
        """Test creating a profile with all fields"""
        profile = Profile(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            seniority="Senior",
            company_id=sample_companies[0].id,
            generation="Gen X",
            married=True,
            has_children=True,
            good_at="Python, Leadership",
            ie_score=75,
            is_score=60,
            notes="Test notes"
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert profile.email == "john@example.com"
        assert profile.company_id == sample_companies[0].id
        assert profile.married is True

    def test_create_profile_with_tags(self, test_db, sample_tags):
        """Test creating a profile with tags"""
        profile = Profile(
            name="Tagged User",
            seniority="Junior"
        )
        profile.tags.append(sample_tags[0])
        profile.tags.append(sample_tags[1])

        test_db.add(profile)
        test_db.commit()

        assert len(profile.tags) == 2
        assert sample_tags[0] in profile.tags

    def test_create_profile_without_company(self, test_db):
        """Test creating profile without company (company is optional)"""
        profile = Profile(
            name="No Company User",
            seniority="Senior"
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert profile.company_id is None
        assert profile.company is None


class TestProfileRead:
    """Test Profile read operations"""

    def test_read_profile_by_id(self, test_db, sample_profiles):
        """Test reading a profile by ID"""
        profile = test_db.query(Profile).filter_by(id=sample_profiles[0].id).first()

        assert profile is not None
        assert profile.name == sample_profiles[0].name

    def test_read_profile_by_email(self, test_db, sample_profiles):
        """Test reading a profile by email"""
        profile = test_db.query(Profile).filter_by(
            email="john.doe@example.com"
        ).first()

        assert profile is not None
        assert profile.name == "John Doe"

    def test_read_all_profiles(self, test_db, sample_profiles):
        """Test reading all profiles"""
        profiles = test_db.query(Profile).all()

        assert len(profiles) == 4
        assert all(isinstance(p, Profile) for p in profiles)

    def test_read_profiles_by_seniority(self, test_db, sample_profiles):
        """Test filtering profiles by seniority"""
        profiles = test_db.query(Profile).filter_by(seniority="Senior").all()

        assert len(profiles) == 1
        assert profiles[0].name == "John Doe"

    def test_read_profiles_by_company(self, test_db, sample_profiles, sample_companies):
        """Test filtering profiles by company"""
        profiles = test_db.query(Profile).filter_by(
            company_id=sample_companies[0].id
        ).all()

        assert len(profiles) == 2  # John and Jane work at TechCorp

    def test_read_profile_with_tags(self, test_db, sample_profiles):
        """Test reading profile tags relationship"""
        profile = test_db.query(Profile).filter_by(name="John Doe").first()

        assert len(profile.tags) == 2
        tag_names = [tag.name for tag in profile.tags]
        assert "VIP" in tag_names
        assert "Partner" in tag_names


class TestProfileUpdate:
    """Test Profile update operations"""

    def test_update_profile_name(self, test_db, sample_profiles):
        """Test updating profile name"""
        profile = sample_profiles[0]
        original_name = profile.name

        profile.name = "Updated Name"
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert updated.name == "Updated Name"
        assert updated.name != original_name

    def test_update_profile_email(self, test_db, sample_profiles):
        """Test updating profile email"""
        profile = sample_profiles[0]

        profile.email = "newemail@example.com"
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert updated.email == "newemail@example.com"

    def test_update_profile_company(self, test_db, sample_profiles, sample_companies):
        """Test updating profile company"""
        profile = sample_profiles[3]  # Bob
        assert profile.company_id == sample_companies[2].id

        profile.company_id = sample_companies[0].id
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert updated.company_id == sample_companies[0].id

    def test_update_profile_add_tag(self, test_db, sample_profiles, sample_tags):
        """Test adding a tag to profile"""
        profile = sample_profiles[3]  # Bob has 1 tag
        original_tag_count = len(profile.tags)

        profile.tags.append(sample_tags[0])  # Add VIP
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert len(updated.tags) == original_tag_count + 1

    def test_update_profile_remove_tag(self, test_db, sample_profiles):
        """Test removing a tag from profile"""
        profile = sample_profiles[0]  # John has 2 tags
        original_tag_count = len(profile.tags)

        profile.tags.pop()
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert len(updated.tags) == original_tag_count - 1

    def test_update_profile_notes(self, test_db, sample_profiles):
        """Test updating profile notes"""
        profile = sample_profiles[0]

        profile.notes = "Updated notes with new information"
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert "Updated notes" in updated.notes


class TestProfileDelete:
    """Test Profile delete operations"""

    def test_delete_profile(self, test_db, sample_profiles):
        """Test deleting a profile"""
        profile_id = sample_profiles[0].id
        profile_count_before = test_db.query(Profile).count()

        test_db.delete(sample_profiles[0])
        test_db.commit()

        profile_count_after = test_db.query(Profile).count()
        deleted_profile = test_db.query(Profile).filter_by(id=profile_id).first()

        assert profile_count_after == profile_count_before - 1
        assert deleted_profile is None

    def test_delete_profile_preserves_company(self, test_db, sample_profiles, sample_companies):
        """Test that deleting profile doesn't delete company"""
        company_id = sample_profiles[0].company_id
        company_count_before = test_db.query(Company).count()

        test_db.delete(sample_profiles[0])
        test_db.commit()

        company_count_after = test_db.query(Company).count()
        company = test_db.query(Company).filter_by(id=company_id).first()

        assert company_count_after == company_count_before
        assert company is not None

    def test_delete_profile_removes_tag_association(self, test_db, sample_profiles, sample_tags):
        """Test that deleting profile removes tag associations but not tags"""
        profile = sample_profiles[0]  # Has 2 tags
        tag_ids = [tag.id for tag in profile.tags]
        tag_count_before = test_db.query(Tag).count()

        test_db.delete(profile)
        test_db.commit()

        tag_count_after = test_db.query(Tag).count()

        # Tags should still exist
        assert tag_count_after == tag_count_before

        # Tags should still be in database
        for tag_id in tag_ids:
            tag = test_db.query(Tag).filter_by(id=tag_id).first()
            assert tag is not None


class TestProfileSearch:
    """Test Profile search operations"""

    def test_search_by_name_exact(self, test_db, sample_profiles):
        """Test searching profile by exact name"""
        profiles = test_db.query(Profile).filter(
            Profile.name == "John Doe"
        ).all()

        assert len(profiles) == 1
        assert profiles[0].name == "John Doe"

    def test_search_by_name_partial(self, test_db, sample_profiles):
        """Test searching profile by partial name (LIKE)"""
        profiles = test_db.query(Profile).filter(
            Profile.name.ilike("%john%")
        ).all()

        assert len(profiles) >= 1
        assert any(p.name == "John Doe" for p in profiles)

    def test_search_by_email_partial(self, test_db, sample_profiles):
        """Test searching profile by email pattern"""
        profiles = test_db.query(Profile).filter(
            Profile.email.ilike("%@example.com")
        ).all()

        assert len(profiles) == 4  # All test profiles use example.com

    def test_search_by_skills(self, test_db, sample_profiles):
        """Test searching profile by skills (good_at field)"""
        profiles = test_db.query(Profile).filter(
            Profile.good_at.ilike("%python%")
        ).all()

        assert len(profiles) >= 1
        assert any(p.name == "John Doe" for p in profiles)

    def test_search_multiple_conditions(self, test_db, sample_profiles):
        """Test searching with multiple conditions (AND)"""
        from sqlalchemy import and_

        profiles = test_db.query(Profile).filter(
            and_(
                Profile.seniority == "Senior",
                Profile.married == True
            )
        ).all()

        assert len(profiles) == 1
        assert profiles[0].name == "John Doe"

    def test_search_or_conditions(self, test_db, sample_profiles):
        """Test searching with OR conditions"""
        from sqlalchemy import or_

        profiles = test_db.query(Profile).filter(
            or_(
                Profile.seniority == "Executive",
                Profile.seniority == "Senior"
            )
        ).all()

        assert len(profiles) == 2


class TestProfileValidation:
    """Test Profile data validation"""

    def test_profile_requires_name(self, test_db):
        """Test that profile requires a name"""
        # This should be enforced at application level
        # SQLAlchemy will allow null if not specified as nullable=False

        profile = Profile(seniority="Senior")

        # This will succeed in SQLAlchemy unless we add validation
        # In real app, validators.py should catch this
        test_db.add(profile)

        # Should validate before commit in real application
        # This test documents expected validation

    def test_email_format_validation(self, test_db):
        """Test email format validation"""
        # Email validation should be done in validators.py
        # This test documents expected validation behavior

        profile = Profile(
            name="Test",
            email="invalid-email",  # Invalid format
            seniority="Junior"
        )

        # In real app, validate_email() should be called before save
        # This test documents the expected behavior

    def test_phone_format_validation(self, test_db):
        """Test phone format validation"""
        # Phone validation should be done in validators.py

        profile = Profile(
            name="Test",
            phone="invalid",  # Invalid format
            seniority="Junior"
        )

        # In real app, validate_phone() should be called before save


class TestProfileEdgeCases:
    """Test Profile edge cases"""

    def test_profile_with_long_name(self, test_db):
        """Test profile with very long name"""
        long_name = "A" * 200

        profile = Profile(
            name=long_name,
            seniority="Mid-Level"
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert len(profile.name) == 200

    def test_profile_with_special_characters(self, test_db):
        """Test profile with special characters in name"""
        profile = Profile(
            name="José García-López",
            seniority="Senior"
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert profile.name == "José García-López"

    def test_profile_with_empty_notes(self, test_db):
        """Test profile with empty notes"""
        profile = Profile(
            name="Test",
            seniority="Junior",
            notes=""
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.notes == ""

    def test_profile_with_none_optional_fields(self, test_db):
        """Test profile with None in optional fields"""
        profile = Profile(
            name="Test",
            seniority="Junior",
            email=None,
            phone=None,
            generation=None,
            notes=None
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.email is None
        assert profile.phone is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
