"""
Unit tests for Tag model — all CRUD operations and every attribute
"""

import pytest
from leadsauce.models.tag import Tag
from leadsauce.models.profile import Profile


class TestTagCreate:
    """Test Tag creation covering every field"""

    def test_create_minimal_tag(self, test_db):
        """Required field only: name"""
        tag = Tag(name="Important")
        test_db.add(tag)
        test_db.commit()

        assert tag.id is not None
        assert tag.name == "Important"
        assert tag.color is None
        assert tag.description is None
        assert tag.created_at is not None
        assert tag.updated_at is not None

    def test_create_full_tag_all_fields(self, test_db):
        """All fields populated"""
        tag = Tag(
            name="VIP Client",
            color="#FF5733",
            description="High value clients requiring priority attention"
        )
        test_db.add(tag)
        test_db.commit()

        assert tag.name == "VIP Client"
        assert tag.color == "#FF5733"
        assert tag.description == "High value clients requiring priority attention"

    def test_create_multiple_tags(self, test_db):
        tags = [Tag(name=f"Tag{i}") for i in range(5)]
        test_db.add_all(tags)
        test_db.commit()
        assert test_db.query(Tag).count() == 5

    def test_tag_color_hex_format(self, test_db):
        """Test various hex color formats"""
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000", "#A1B2C3"]
        for color in colors:
            t = Tag(name=f"Tag {color}", color=color)
            test_db.add(t)
        test_db.commit()
        results = test_db.query(Tag).all()
        stored_colors = [t.color for t in results if t.color]
        for color in colors:
            assert color in stored_colors

    def test_tag_name_unique_constraint(self, test_db):
        """Tag names must be unique"""
        t1 = Tag(name="Unique Tag")
        test_db.add(t1)
        test_db.commit()

        t2 = Tag(name="Unique Tag")
        test_db.add(t2)
        with pytest.raises(Exception):
            test_db.commit()
        test_db.rollback()


class TestTagRead:
    """Test Tag read/query operations"""

    def test_read_by_id(self, test_db, sample_tags):
        t = test_db.query(Tag).filter_by(id=sample_tags[0].id).first()
        assert t is not None
        assert t.name == "VIP"

    def test_read_by_name(self, test_db, sample_tags):
        t = test_db.query(Tag).filter_by(name="Lead").first()
        assert t is not None
        assert t.color == "#0000FF"

    def test_read_all_tags(self, test_db, sample_tags):
        all_tags = test_db.query(Tag).all()
        assert len(all_tags) == 4

    def test_read_by_color(self, test_db, sample_tags):
        red_tags = test_db.query(Tag).filter_by(color="#FF0000").all()
        assert len(red_tags) == 1
        assert red_tags[0].name == "VIP"

    def test_read_tag_profiles(self, test_db, sample_profiles, sample_tags):
        vip_tag = test_db.query(Tag).filter_by(name="VIP").first()
        assert len(vip_tag.profiles) == 2

    def test_read_tag_with_no_profiles(self, test_db):
        t = Tag(name="Orphan Tag")
        test_db.add(t)
        test_db.commit()
        assert len(t.profiles) == 0

    def test_read_tag_description(self, test_db, sample_tags):
        t = test_db.query(Tag).filter_by(name="VIP").first()
        assert t.description == "VIP contact"


class TestTagUpdate:
    """Test Tag update operations"""

    def test_update_name(self, test_db, sample_tags):
        t = sample_tags[0]
        t.name = "VIP Premium"
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().name == "VIP Premium"

    def test_update_color(self, test_db, sample_tags):
        t = sample_tags[0]
        t.color = "#FF6600"
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().color == "#FF6600"

    def test_update_description(self, test_db, sample_tags):
        t = sample_tags[1]
        t.description = "Updated: Active sales leads in pipeline"
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().description == "Updated: Active sales leads in pipeline"

    def test_clear_color(self, test_db, sample_tags):
        t = sample_tags[0]
        t.color = None
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().color is None

    def test_clear_description(self, test_db, sample_tags):
        t = sample_tags[0]
        t.description = None
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().description is None


class TestTagDelete:
    """Test Tag deletion"""

    def test_delete_tag(self, test_db, sample_tags):
        tid = sample_tags[3].id
        test_db.delete(sample_tags[3])
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=tid).first() is None

    def test_delete_tag_preserves_profiles(self, test_db, sample_profiles, sample_tags):
        """Deleting a tag must not delete profiles"""
        tag = sample_tags[0]
        profile_ids = [p.id for p in tag.profiles]
        test_db.delete(tag)
        test_db.commit()
        for pid in profile_ids:
            assert test_db.query(Profile).filter_by(id=pid).first() is not None

    def test_delete_tag_removes_association(self, test_db, sample_profiles, sample_tags):
        """After deleting a tag, profiles no longer have it"""
        tag = sample_tags[0]
        profile = tag.profiles[0]
        pid = profile.id
        test_db.delete(tag)
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=pid).first()
        tag_names = [t.name for t in refreshed.tags]
        assert "VIP" not in tag_names


class TestTagToDict:
    """Test Tag serialization"""

    def test_to_dict_basic(self, test_db, sample_tags):
        t = sample_tags[0]
        d = t.to_dict()
        assert d['name'] == t.name
        assert d['color'] == t.color
        assert 'description' in d

    def test_to_dict_with_count(self, test_db, sample_profiles, sample_tags):
        t = sample_tags[0]
        d = t.to_dict(include_count=True)
        assert 'profile_count' in d or 'count' in d


class TestTagEdgeCases:
    """Edge cases"""

    def test_tag_name_with_spaces(self, test_db):
        t = Tag(name="High Priority Client")
        test_db.add(t)
        test_db.commit()
        assert test_db.query(Tag).filter_by(name="High Priority Client").first() is not None

    def test_tag_name_with_special_chars(self, test_db):
        t = Tag(name="Q4/2024-Target")
        test_db.add(t)
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().name == "Q4/2024-Target"

    def test_tag_search_partial_name(self, test_db, sample_tags):
        results = test_db.query(Tag).filter(Tag.name.ilike("%vip%")).all()
        assert len(results) >= 1

    def test_tag_max_name_length(self, test_db):
        long_name = "T" * 100
        t = Tag(name=long_name)
        test_db.add(t)
        test_db.commit()
        assert test_db.query(Tag).filter_by(id=t.id).first().name == long_name
