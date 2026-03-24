"""
Unit tests for Company model — all CRUD operations and every attribute
"""

import pytest
from leadsauce.models.company import Company
from leadsauce.models.profile import Profile


class TestCompanyCreate:
    """Test Company creation covering every field"""

    def test_create_minimal_company(self, test_db):
        """Required field only: name"""
        company = Company(name="Minimal Corp")
        test_db.add(company)
        test_db.commit()

        assert company.id is not None
        assert company.name == "Minimal Corp"
        assert company.industry is None
        assert company.size is None
        assert company.location is None
        assert company.website is None
        assert company.notes is None
        assert company.created_at is not None
        assert company.updated_at is not None

    def test_create_full_company_all_fields(self, test_db):
        """All fields populated"""
        company = Company(
            name="FullStack Ltd",
            industry="Technology",
            size="500-1000",
            location="Berlin, Germany",
            website="https://fullstack.example.com",
            notes="Main enterprise client"
        )
        test_db.add(company)
        test_db.commit()

        assert company.name == "FullStack Ltd"
        assert company.industry == "Technology"
        assert company.size == "500-1000"
        assert company.location == "Berlin, Germany"
        assert company.website == "https://fullstack.example.com"
        assert company.notes == "Main enterprise client"

    def test_create_multiple_companies(self, test_db):
        companies = [
            Company(name="Alpha Inc", industry="Finance"),
            Company(name="Beta LLC", industry="Healthcare"),
            Company(name="Gamma Corp", industry="Retail"),
        ]
        test_db.add_all(companies)
        test_db.commit()
        assert test_db.query(Company).count() == 3

    def test_company_size_variants(self, test_db):
        sizes = ["1-10", "10-50", "50-200", "200-500", "500-1000", "1000-5000", "5000+"]
        for size in sizes:
            c = Company(name=f"Company {size}", size=size)
            test_db.add(c)
        test_db.commit()
        results = test_db.query(Company).all()
        size_values = [c.size for c in results]
        for size in sizes:
            assert size in size_values


class TestCompanyRead:
    """Test Company read/query operations"""

    def test_read_by_id(self, test_db, sample_companies):
        c = test_db.query(Company).filter_by(id=sample_companies[0].id).first()
        assert c is not None
        assert c.name == "TechCorp Inc"

    def test_read_by_name(self, test_db, sample_companies):
        c = test_db.query(Company).filter_by(name="DesignStudio LLC").first()
        assert c is not None

    def test_read_all_companies(self, test_db, sample_companies):
        all_companies = test_db.query(Company).all()
        assert len(all_companies) == 3

    def test_read_by_industry(self, test_db, sample_companies):
        tech = test_db.query(Company).filter_by(industry="Technology").all()
        assert len(tech) == 1
        assert tech[0].name == "TechCorp Inc"

    def test_read_by_size(self, test_db, sample_companies):
        large = test_db.query(Company).filter_by(size="5000+").all()
        assert len(large) == 1
        assert large[0].name == "FinanceGlobal"

    def test_read_by_location(self, test_db, sample_companies):
        ny = test_db.query(Company).filter(Company.location.ilike("%New York%")).all()
        assert len(ny) == 1
        assert ny[0].name == "DesignStudio LLC"

    def test_read_profiles_relationship(self, test_db, sample_profiles, sample_companies):
        c = test_db.query(Company).filter_by(id=sample_companies[0].id).first()
        assert len(c.profiles) == 2

    def test_read_company_with_no_profiles(self, test_db):
        c = Company(name="Empty Corp")
        test_db.add(c)
        test_db.commit()
        assert len(c.profiles) == 0


class TestCompanyUpdate:
    """Test Company update operations"""

    def test_update_name(self, test_db, sample_companies):
        c = sample_companies[0]
        c.name = "TechCorp Renamed"
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().name == "TechCorp Renamed"

    def test_update_industry(self, test_db, sample_companies):
        c = sample_companies[1]
        c.industry = "Creative Technology"
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().industry == "Creative Technology"

    def test_update_size(self, test_db, sample_companies):
        c = sample_companies[1]
        c.size = "50-200"
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().size == "50-200"

    def test_update_location(self, test_db, sample_companies):
        c = sample_companies[0]
        c.location = "Austin, TX"
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().location == "Austin, TX"

    def test_update_website(self, test_db, sample_companies):
        c = sample_companies[0]
        c.website = "https://new-techcorp.example.com"
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().website == "https://new-techcorp.example.com"

    def test_update_notes(self, test_db, sample_companies):
        c = sample_companies[0]
        c.notes = "Updated notes after quarterly review"
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().notes == "Updated notes after quarterly review"

    def test_clear_optional_field(self, test_db, sample_companies):
        c = sample_companies[0]
        c.website = None
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().website is None


class TestCompanyDelete:
    """Test Company deletion"""

    def test_delete_company(self, test_db, sample_companies):
        cid = sample_companies[2].id
        test_db.delete(sample_companies[2])
        test_db.commit()
        assert test_db.query(Company).filter_by(id=cid).first() is None

    def test_delete_company_sets_profile_company_null(self, test_db, sample_profiles, sample_companies):
        """Deleting a company should set profile.company_id to NULL (SET NULL)"""
        company = sample_companies[0]
        cid = company.id
        profile_ids = [p.id for p in company.profiles]
        test_db.delete(company)
        test_db.commit()
        for pid in profile_ids:
            p = test_db.query(Profile).filter_by(id=pid).first()
            assert p is not None
            assert p.company_id is None

    def test_delete_all_companies(self, test_db, sample_companies):
        for c in sample_companies:
            test_db.delete(c)
        test_db.commit()
        assert test_db.query(Company).count() == 0


class TestCompanyToDict:
    """Test Company serialization"""

    def test_to_dict_all_fields(self, test_db, sample_companies):
        c = sample_companies[0]
        d = c.to_dict()
        assert d['name'] == c.name
        assert d['industry'] == c.industry
        assert d['size'] == c.size
        assert d['location'] == c.location
        assert d['website'] == c.website
        assert d['notes'] == c.notes

    def test_to_dict_with_profiles(self, test_db, sample_profiles, sample_companies):
        c = sample_companies[0]
        d = c.to_dict(include_profiles=True)
        assert 'profiles' in d


class TestCompanyEdgeCases:
    """Edge cases"""

    def test_company_with_long_name(self, test_db):
        name = "A" * 255
        c = Company(name=name)
        test_db.add(c)
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().name == name

    def test_company_search_partial_name(self, test_db, sample_companies):
        results = test_db.query(Company).filter(Company.name.ilike("%tech%")).all()
        assert len(results) >= 1

    def test_company_search_partial_industry(self, test_db, sample_companies):
        results = test_db.query(Company).filter(Company.industry.ilike("%fin%")).all()
        assert len(results) == 1
        assert results[0].name == "FinanceGlobal"

    def test_company_with_special_characters(self, test_db):
        c = Company(name="O'Brien & Sons LLC", location="Dublin, Ireland")
        test_db.add(c)
        test_db.commit()
        assert test_db.query(Company).filter_by(id=c.id).first().name == "O'Brien & Sons LLC"
