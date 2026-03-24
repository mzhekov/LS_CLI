"""
Unit tests for Profile model — all CRUD operations and every attribute
"""

import pytest
from datetime import datetime
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag


class TestProfileCreate:
    """Test Profile creation covering every field"""

    def test_create_minimal_profile(self, test_db):
        """Required fields only: name + seniority"""
        profile = Profile(name="Test User", seniority="Mid-Level")
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert profile.name == "Test User"
        assert profile.seniority == "Mid-Level"
        assert profile.email is None
        assert profile.phone is None
        assert profile.married is False
        assert profile.has_children is False
        assert profile.interaction_count == 0
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_create_full_profile_all_fields(self, test_db, sample_companies):
        """All fields populated"""
        profile = Profile(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            seniority="Senior",
            company_id=sample_companies[0].id,
            generation="Gen X",
            married=True,
            has_children=True,
            ie_score=75,
            is_score=60,
            good_at="Python, Leadership",
            need_to_work="Delegation",
            work_for="Innovation and impact",
            additional_info="Met at TechConf 2024",
            notes="Great contact"
        )
        test_db.add(profile)
        test_db.commit()

        assert profile.id is not None
        assert profile.name == "John Doe"
        assert profile.email == "john@example.com"
        assert profile.phone == "+1234567890"
        assert profile.seniority == "Senior"
        assert profile.company_id == sample_companies[0].id
        assert profile.generation == "Gen X"
        assert profile.married is True
        assert profile.has_children is True
        assert profile.ie_score == 75
        assert profile.is_score == 60
        assert profile.good_at == "Python, Leadership"
        assert profile.need_to_work == "Delegation"
        assert profile.work_for == "Innovation and impact"
        assert profile.additional_info == "Met at TechConf 2024"
        assert profile.notes == "Great contact"

    def test_create_profile_with_tags(self, test_db, sample_tags):
        """Profile linked to multiple tags"""
        profile = Profile(name="Tagged User", seniority="Junior")
        profile.tags.append(sample_tags[0])
        profile.tags.append(sample_tags[1])
        test_db.add(profile)
        test_db.commit()

        assert len(profile.tags) == 2
        assert sample_tags[0] in profile.tags
        assert sample_tags[1] in profile.tags

    def test_create_profile_without_company(self, test_db):
        """Profile with no company assigned"""
        profile = Profile(name="Freelancer", seniority="Senior")
        test_db.add(profile)
        test_db.commit()

        assert profile.company_id is None
        assert profile.company is None

    def test_create_profile_all_seniority_levels(self, test_db):
        """Profile with each seniority level"""
        from leadsauce.utils.constants import SENIORITY_LEVELS
        for level in SENIORITY_LEVELS:
            p = Profile(name=f"User {level}", seniority=level)
            test_db.add(p)
        test_db.commit()

        results = test_db.query(Profile).all()
        seniority_values = [p.seniority for p in results]
        for level in SENIORITY_LEVELS:
            assert level in seniority_values

    def test_create_profile_all_generation_types(self, test_db):
        """Profile with each generation type"""
        from leadsauce.utils.constants import GENERATION_TYPES
        for gen in GENERATION_TYPES:
            p = Profile(name=f"User {gen}", seniority="Mid-Level", generation=gen)
            test_db.add(p)
        test_db.commit()

        results = test_db.query(Profile).filter(Profile.generation.isnot(None)).all()
        gen_values = [p.generation for p in results]
        for gen in GENERATION_TYPES:
            assert gen in gen_values

    def test_ie_score_boundary_values(self, test_db):
        """ie_score and is_score at 0 and 100"""
        p_min = Profile(name="Introvert Min", seniority="Junior", ie_score=0, is_score=0)
        p_max = Profile(name="Extrovert Max", seniority="Senior", ie_score=100, is_score=100)
        test_db.add_all([p_min, p_max])
        test_db.commit()

        assert p_min.ie_score == 0
        assert p_min.is_score == 0
        assert p_max.ie_score == 100
        assert p_max.is_score == 100

    def test_profile_defaults(self, test_db):
        """Verify all default values are applied"""
        profile = Profile(name="Defaults Test", seniority="Junior")
        test_db.add(profile)
        test_db.commit()

        assert profile.married is False
        assert profile.has_children is False
        assert profile.interaction_count == 0
        assert profile.ie_score is None
        assert profile.is_score is None
        assert profile.last_contact is None


class TestProfileRead:
    """Test Profile read/query operations"""

    def test_read_by_id(self, test_db, sample_profiles):
        p = test_db.query(Profile).filter_by(id=sample_profiles[0].id).first()
        assert p is not None
        assert p.name == sample_profiles[0].name

    def test_read_by_email(self, test_db, sample_profiles):
        p = test_db.query(Profile).filter_by(email="john.doe@example.com").first()
        assert p is not None
        assert p.name == "John Doe"

    def test_read_all_profiles(self, test_db, sample_profiles):
        profiles = test_db.query(Profile).all()
        assert len(profiles) == len(sample_profiles)

    def test_read_by_seniority(self, test_db, sample_profiles):
        seniors = test_db.query(Profile).filter_by(seniority="Senior").all()
        assert len(seniors) == 1
        assert seniors[0].name == "John Doe"

    def test_read_by_company(self, test_db, sample_profiles, sample_companies):
        profiles = test_db.query(Profile).filter_by(company_id=sample_companies[0].id).all()
        assert len(profiles) == 2

    def test_read_with_tags(self, test_db, sample_profiles):
        p = test_db.query(Profile).filter_by(name="John Doe").first()
        assert len(p.tags) == 2
        tag_names = [t.name for t in p.tags]
        assert "VIP" in tag_names
        assert "Partner" in tag_names

    def test_read_by_generation(self, test_db, sample_profiles):
        gen_z = test_db.query(Profile).filter_by(generation="Gen Z").all()
        assert len(gen_z) == 1
        assert gen_z[0].name == "Bob Wilson"

    def test_read_married_profiles(self, test_db, sample_profiles):
        married = test_db.query(Profile).filter_by(married=True).all()
        assert len(married) == 2

    def test_read_profiles_with_children(self, test_db, sample_profiles):
        with_children = test_db.query(Profile).filter_by(has_children=True).all()
        assert len(with_children) == 1
        assert with_children[0].name == "John Doe"


class TestProfileUpdate:
    """Test Profile update operations"""

    def test_update_name(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.name = "John Updated"
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=p.id).first()
        assert refreshed.name == "John Updated"

    def test_update_email(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.email = "new.email@example.com"
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=p.id).first()
        assert refreshed.email == "new.email@example.com"

    def test_update_phone(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.phone = "+9999999999"
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().phone == "+9999999999"

    def test_update_seniority(self, test_db, sample_profiles):
        p = sample_profiles[3]
        p.seniority = "Mid-Level"
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().seniority == "Mid-Level"

    def test_update_company(self, test_db, sample_profiles, sample_companies):
        p = sample_profiles[3]
        p.company_id = sample_companies[0].id
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().company_id == sample_companies[0].id

    def test_update_married_status(self, test_db, sample_profiles):
        p = sample_profiles[1]
        assert p.married is False
        p.married = True
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().married is True

    def test_update_has_children(self, test_db, sample_profiles):
        p = sample_profiles[1]
        p.has_children = True
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().has_children is True

    def test_update_ie_is_scores(self, test_db, sample_profiles):
        p = sample_profiles[2]
        p.ie_score = 45
        p.is_score = 55
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=p.id).first()
        assert refreshed.ie_score == 45
        assert refreshed.is_score == 55

    def test_update_good_at(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.good_at = "Python, Leadership, Public Speaking"
        test_db.commit()
        assert "Public Speaking" in test_db.query(Profile).filter_by(id=p.id).first().good_at

    def test_update_need_to_work(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.need_to_work = "Time management, Patience"
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().need_to_work == "Time management, Patience"

    def test_update_work_for(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.work_for = "Financial freedom"
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().work_for == "Financial freedom"

    def test_update_notes(self, test_db, sample_profiles):
        p = sample_profiles[0]
        p.notes = "Updated notes after meeting"
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().notes == "Updated notes after meeting"

    def test_add_tag_to_profile(self, test_db, sample_profiles, sample_tags):
        p = sample_profiles[3]
        initial_count = len(p.tags)
        p.tags.append(sample_tags[2])
        test_db.commit()
        assert len(test_db.query(Profile).filter_by(id=p.id).first().tags) == initial_count + 1

    def test_remove_tag_from_profile(self, test_db, sample_profiles, sample_tags):
        p = sample_profiles[0]
        initial_count = len(p.tags)
        p.tags.remove(sample_tags[0])
        test_db.commit()
        assert len(test_db.query(Profile).filter_by(id=p.id).first().tags) == initial_count - 1

    def test_update_last_contact(self, test_db, sample_profiles):
        from leadsauce.models.interaction import Interaction
        p = sample_profiles[0]
        interaction = Interaction(profile_id=p.id, interaction_type="call", notes="Test call")
        test_db.add(interaction)
        test_db.commit()
        test_db.refresh(p)
        p.update_last_contact()
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=p.id).first()
        assert refreshed.last_contact is not None
        assert refreshed.interaction_count == 1

    def test_update_interaction_count_increments(self, test_db, sample_profiles):
        from leadsauce.models.interaction import Interaction
        p = sample_profiles[0]
        for _ in range(2):
            interaction = Interaction(profile_id=p.id, interaction_type="email", notes="Test")
            test_db.add(interaction)
        test_db.commit()
        test_db.refresh(p)
        p.update_last_contact()
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().interaction_count == 2


class TestProfileDelete:
    """Test Profile deletion"""

    def test_delete_profile(self, test_db, sample_profiles):
        pid = sample_profiles[0].id
        test_db.delete(sample_profiles[0])
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=pid).first() is None

    def test_delete_profile_preserves_company(self, test_db, sample_profiles, sample_companies):
        test_db.delete(sample_profiles[0])
        test_db.commit()
        assert test_db.query(Company).filter_by(id=sample_companies[0].id).first() is not None

    def test_delete_profile_removes_tag_associations(self, test_db, sample_profiles, sample_tags):
        p = sample_profiles[0]
        pid = p.id
        test_db.delete(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=pid).first() is None
        # Tags themselves should still exist
        assert test_db.query(Tag).filter_by(name="VIP").first() is not None

    def test_delete_all_profiles(self, test_db, sample_profiles):
        for p in sample_profiles:
            test_db.delete(p)
        test_db.commit()
        assert test_db.query(Profile).count() == 0


class TestProfileSearch:
    """Test profile search and filter queries"""

    def test_search_by_exact_name(self, test_db, sample_profiles):
        results = test_db.query(Profile).filter(Profile.name == "John Doe").all()
        assert len(results) == 1

    def test_search_by_partial_name(self, test_db, sample_profiles):
        results = test_db.query(Profile).filter(Profile.name.ilike("%john%")).all()
        assert len(results) >= 1

    def test_search_by_email_pattern(self, test_db, sample_profiles):
        results = test_db.query(Profile).filter(Profile.email.ilike("%example.com%")).all()
        assert len(results) == 4

    def test_search_by_skills(self, test_db, sample_profiles):
        results = test_db.query(Profile).filter(Profile.good_at.ilike("%Python%")).all()
        assert len(results) == 1
        assert results[0].name == "John Doe"

    def test_search_multiple_conditions(self, test_db, sample_profiles, sample_companies):
        results = test_db.query(Profile).filter(
            Profile.seniority == "Senior",
            Profile.company_id == sample_companies[0].id
        ).all()
        assert len(results) == 1

    def test_search_by_generation(self, test_db, sample_profiles):
        results = test_db.query(Profile).filter(Profile.generation == "Millennial").all()
        assert len(results) == 1
        assert results[0].name == "Alice Johnson"

    def test_search_no_results(self, test_db, sample_profiles):
        results = test_db.query(Profile).filter(Profile.name == "Nobody Here").all()
        assert len(results) == 0


class TestProfileToDict:
    """Test Profile serialization"""

    def test_to_dict_basic(self, test_db, sample_profiles):
        p = sample_profiles[0]
        d = p.to_dict()
        assert d['name'] == p.name
        assert d['email'] == p.email
        assert d['seniority'] == p.seniority
        assert d['phone'] == p.phone
        assert d['generation'] == p.generation
        assert d['married'] == p.married
        assert d['has_children'] == p.has_children
        assert d['ie_score'] == p.ie_score
        assert d['is_score'] == p.is_score
        assert d['good_at'] == p.good_at
        assert d['notes'] == p.notes

    def test_to_dict_with_relations(self, test_db, sample_profiles):
        p = sample_profiles[0]
        d = p.to_dict(include_relations=True)
        assert 'tags' in d or 'company' in d


class TestProfileEdgeCases:
    """Edge cases and boundary conditions"""

    def test_profile_with_very_long_name(self, test_db):
        long_name = "A" * 255
        p = Profile(name=long_name, seniority="Junior")
        test_db.add(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().name == long_name

    def test_profile_with_special_characters_in_name(self, test_db):
        p = Profile(name="María José O'Brien-López", seniority="Mid-Level")
        test_db.add(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().name == "María José O'Brien-López"

    def test_profile_with_empty_notes(self, test_db):
        p = Profile(name="Empty Notes", seniority="Senior", notes="")
        test_db.add(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().notes == ""

    def test_profile_with_none_optional_fields(self, test_db):
        p = Profile(
            name="Minimal",
            seniority="Junior",
            email=None,
            phone=None,
            generation=None,
            ie_score=None,
            is_score=None,
            good_at=None,
            notes=None
        )
        test_db.add(p)
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=p.id).first()
        assert refreshed.email is None
        assert refreshed.phone is None
        assert refreshed.generation is None
        assert refreshed.ie_score is None
        assert refreshed.is_score is None

    def test_two_profiles_same_company(self, test_db, sample_companies):
        p1 = Profile(name="Employee One", seniority="Junior", company_id=sample_companies[0].id)
        p2 = Profile(name="Employee Two", seniority="Senior", company_id=sample_companies[0].id)
        test_db.add_all([p1, p2])
        test_db.commit()
        count = test_db.query(Profile).filter_by(company_id=sample_companies[0].id).count()
        assert count == 2

    def test_profile_additional_info_field(self, test_db):
        info = "Met at Conference 2024, referred by Alice, interested in blockchain"
        p = Profile(name="Info User", seniority="Mid-Level", additional_info=info)
        test_db.add(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().additional_info == info

    def test_profile_need_to_work_field(self, test_db):
        p = Profile(name="Growth User", seniority="Junior", need_to_work="Communication, Confidence")
        test_db.add(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().need_to_work == "Communication, Confidence"

    def test_profile_work_for_field(self, test_db):
        p = Profile(name="Motivated User", seniority="Senior", work_for="Making an impact")
        test_db.add(p)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=p.id).first().work_for == "Making an impact"
