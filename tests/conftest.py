"""
Pytest configuration and fixtures for LeadSauce CLI tests
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from leadsauce.utils.db import Base
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag
from leadsauce.models.task import Task
from leadsauce.models.goal import Goal
from leadsauce.models.reminder import Reminder
from leadsauce.models.interaction import Interaction
from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship


@pytest.fixture(scope='function')
def test_db():
    """Create a temporary in-memory test database for each test"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def sample_companies(test_db):
    companies = [
        Company(
            name="TechCorp Inc",
            industry="Technology",
            size="1000-5000",
            location="San Francisco, CA",
            website="https://techcorp.example.com",
            notes="Leading tech company"
        ),
        Company(
            name="DesignStudio LLC",
            industry="Design",
            size="10-50",
            location="New York, NY",
            website="https://designstudio.example.com",
            notes="Creative agency"
        ),
        Company(
            name="FinanceGlobal",
            industry="Finance",
            size="5000+",
            location="London, UK",
            notes="Global finance corporation"
        )
    ]
    for c in companies:
        test_db.add(c)
    test_db.commit()
    return companies


@pytest.fixture
def sample_tags(test_db):
    tags = [
        Tag(name="VIP", color="#FF0000", description="VIP contact"),
        Tag(name="Lead", color="#0000FF", description="Sales lead"),
        Tag(name="Partner", color="#00FF00", description="Business partner"),
        Tag(name="Prospect", color="#FFFF00", description="Potential prospect"),
    ]
    for t in tags:
        test_db.add(t)
    test_db.commit()
    return tags


@pytest.fixture
def sample_profiles(test_db, sample_companies, sample_tags):
    profiles = [
        Profile(
            name="John Doe",
            email="john.doe@example.com",
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
            work_for="Innovation",
            additional_info="Met at TechConf 2024",
            notes="Great contact for tech partnerships"
        ),
        Profile(
            name="Jane Smith",
            email="jane.smith@example.com",
            phone="+1234567891",
            seniority="Executive",
            company_id=sample_companies[0].id,
            generation="Boomer",
            married=False,
            has_children=False,
            ie_score=80,
            is_score=55,
            good_at="Strategy, Networking",
            notes="CEO connections"
        ),
        Profile(
            name="Alice Johnson",
            email="alice.j@example.com",
            seniority="Mid-Level",
            company_id=sample_companies[1].id,
            generation="Millennial",
            married=True,
            has_children=False,
            good_at="Design, UX",
            notes="Creative director"
        ),
        Profile(
            name="Bob Wilson",
            email="bob.wilson@example.com",
            seniority="Junior",
            company_id=sample_companies[2].id,
            generation="Gen Z",
            married=False,
            has_children=False,
            good_at="Data Analysis, SQL"
        )
    ]
    profiles[0].tags.append(sample_tags[0])
    profiles[0].tags.append(sample_tags[2])
    profiles[1].tags.append(sample_tags[0])
    profiles[2].tags.append(sample_tags[1])
    profiles[3].tags.append(sample_tags[3])
    for p in profiles:
        test_db.add(p)
    test_db.commit()
    return profiles


@pytest.fixture
def sample_tasks(test_db, sample_profiles, sample_companies, sample_tags):
    tasks = [
        Task(
            title="Follow up with John",
            description="Discuss Q4 partnership",
            status="pending",
            priority="high",
            due_date=datetime.now() + timedelta(days=7)
        ),
        Task(
            title="Send proposal to Jane",
            description="Executive meeting proposal",
            status="in_progress",
            priority="high",
            due_date=datetime.now() + timedelta(days=3)
        ),
        Task(
            title="Review Alice's design",
            description="Website redesign mockups",
            status="completed",
            priority="medium",
            due_date=datetime.now() - timedelta(days=2),
            completed_at=datetime.now() - timedelta(days=1)
        ),
        Task(
            title="Coffee with Bob",
            description="Casual networking",
            status="pending",
            priority="low",
            due_date=datetime.now() + timedelta(days=14)
        ),
        Task(
            title="Overdue report",
            description="Late quarterly report",
            status="pending",
            priority="urgent",
            due_date=datetime.now() - timedelta(days=5)
        )
    ]
    tasks[0].profiles.append(sample_profiles[0])
    tasks[1].profiles.append(sample_profiles[1])
    tasks[2].profiles.append(sample_profiles[2])
    tasks[3].profiles.append(sample_profiles[3])
    tasks[0].companies.append(sample_companies[0])
    tasks[0].tags.append(sample_tags[0])
    for t in tasks:
        test_db.add(t)
    test_db.commit()
    return tasks


@pytest.fixture
def sample_goals(test_db, sample_tasks, sample_profiles, sample_companies, sample_tags):
    goals = [
        Goal(
            title="Expand Tech Partnerships",
            description="Build 5 new partnerships in tech sector",
            status="active",
            priority="high",
            progress=40.0,
            target_date=datetime.now() + timedelta(days=90)
        ),
        Goal(
            title="Executive Network Growth",
            description="Connect with 10 C-level executives",
            status="active",
            priority="medium",
            progress=70.0,
            target_date=datetime.now() + timedelta(days=60)
        ),
        Goal(
            title="Design Collaboration",
            description="Complete 3 design projects",
            status="completed",
            priority="low",
            progress=100.0,
            completed_at=datetime.now() - timedelta(days=5)
        ),
        Goal(
            title="Overdue Goal",
            description="This goal is past its target date",
            status="active",
            priority="high",
            progress=20.0,
            target_date=datetime.now() - timedelta(days=10)
        )
    ]
    goals[0].tasks.append(sample_tasks[0])
    goals[0].profiles.append(sample_profiles[0])
    goals[0].companies.append(sample_companies[0])
    goals[0].tags.append(sample_tags[0])
    goals[1].tasks.append(sample_tasks[1])
    goals[1].profiles.append(sample_profiles[1])
    goals[2].tasks.append(sample_tasks[2])
    goals[2].profiles.append(sample_profiles[2])
    for g in goals:
        test_db.add(g)
    test_db.commit()
    return goals


@pytest.fixture
def sample_reminders(test_db, sample_profiles, sample_companies, sample_tasks, sample_goals):
    reminders = [
        Reminder(
            title="Call John about partnership",
            message="Discuss Q4 strategy",
            reminder_date=datetime.now() + timedelta(days=1),
            priority="high",
            category="call",
            profile_id=sample_profiles[0].id,
            is_recurring=True,
            recurrence_pattern="weekly"
        ),
        Reminder(
            title="Email Jane quarterly report",
            message="Attach metrics spreadsheet",
            reminder_date=datetime.now() + timedelta(days=7),
            priority="medium",
            category="email",
            profile_id=sample_profiles[1].id,
            is_recurring=True,
            recurrence_pattern="monthly"
        ),
        Reminder(
            title="Overdue review",
            message="Review Alice's portfolio",
            reminder_date=datetime.now() - timedelta(days=1),
            priority="high",
            category="meeting",
            profile_id=sample_profiles[2].id
        ),
        Reminder(
            title="Company follow-up",
            message="Follow up with TechCorp",
            reminder_date=datetime.now() + timedelta(days=3),
            priority="low",
            category="follow-up",
            company_id=sample_companies[0].id
        ),
    ]
    for r in reminders:
        test_db.add(r)
    test_db.commit()
    return reminders


@pytest.fixture
def sample_profile_relationships(test_db, sample_profiles):
    rels = [
        ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[1].id,
            relationship_type="Colleague",
            bidirectional=True,
            status="Good",
            description="Work colleagues at TechCorp"
        ),
        ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[2].id,
            relationship_type="Mentor",
            bidirectional=False,
            status="Good",
            description="John mentors Alice"
        ),
        ProfileRelationship(
            from_profile_id=sample_profiles[2].id,
            to_profile_id=sample_profiles[3].id,
            relationship_type="Friend",
            bidirectional=True,
            status="Good"
        ),
        ProfileRelationship(
            from_profile_id=sample_profiles[1].id,
            to_profile_id=sample_profiles[3].id,
            relationship_type="Reports To",
            bidirectional=False,
            status="No Interest"
        ),
    ]
    for r in rels:
        test_db.add(r)
    test_db.commit()
    return rels


@pytest.fixture
def sample_company_relationships(test_db, sample_companies):
    rels = [
        CompanyRelationship(
            from_company_id=sample_companies[0].id,
            to_company_id=sample_companies[1].id,
            relationship_type="Partner",
            bidirectional=True,
            status="Good",
            description="Strategic design partnership"
        ),
        CompanyRelationship(
            from_company_id=sample_companies[0].id,
            to_company_id=sample_companies[2].id,
            relationship_type="Client",
            bidirectional=False,
            status="Good"
        ),
        CompanyRelationship(
            from_company_id=sample_companies[1].id,
            to_company_id=sample_companies[2].id,
            relationship_type="Competitor",
            bidirectional=True,
            status="Bad"
        ),
    ]
    for r in rels:
        test_db.add(r)
    test_db.commit()
    return rels


@pytest.fixture
def mock_console():
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_questionary():
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.text.return_value.ask.return_value = "test input"
    mock.select.return_value.ask.return_value = "test selection"
    mock.confirm.return_value.ask.return_value = True
    mock.press_any_key_to_continue.return_value.ask.return_value = None
    return mock
