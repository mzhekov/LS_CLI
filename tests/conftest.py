"""
Pytest configuration and fixtures for LeadSauce CLI tests
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from leadsauce.models.base import Base
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
    """Create a temporary test database for each test"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Create engine and session
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup
    session.close()
    engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def sample_companies(test_db):
    """Create sample companies for testing"""
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

    for company in companies:
        test_db.add(company)

    test_db.commit()

    return companies


@pytest.fixture
def sample_tags(test_db):
    """Create sample tags for testing"""
    tags = [
        Tag(name="VIP", color="red"),
        Tag(name="Lead", color="blue"),
        Tag(name="Partner", color="green"),
        Tag(name="Prospect", color="yellow")
    ]

    for tag in tags:
        test_db.add(tag)

    test_db.commit()

    return tags


@pytest.fixture
def sample_profiles(test_db, sample_companies, sample_tags):
    """Create sample profiles for testing"""
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
            good_at="Python, Leadership",
            ie_score=75,
            is_score=60,
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
            good_at="Strategy, Networking",
            ie_score=80,
            is_score=55,
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

    # Add tags to some profiles
    profiles[0].tags.append(sample_tags[0])  # VIP
    profiles[0].tags.append(sample_tags[2])  # Partner
    profiles[1].tags.append(sample_tags[0])  # VIP
    profiles[2].tags.append(sample_tags[1])  # Lead
    profiles[3].tags.append(sample_tags[3])  # Prospect

    for profile in profiles:
        test_db.add(profile)

    test_db.commit()

    return profiles


@pytest.fixture
def sample_tasks(test_db, sample_profiles):
    """Create sample tasks for testing"""
    from datetime import datetime, timedelta

    tasks = [
        Task(
            title="Follow up with John",
            description="Discuss Q4 partnership",
            status="Pending",
            priority="High",
            due_date=datetime.now() + timedelta(days=7)
        ),
        Task(
            title="Send proposal to Jane",
            description="Executive meeting proposal",
            status="In Progress",
            priority="High",
            due_date=datetime.now() + timedelta(days=3)
        ),
        Task(
            title="Review Alice's design",
            description="Website redesign mockups",
            status="Completed",
            priority="Medium",
            due_date=datetime.now() - timedelta(days=2),
            completed_at=datetime.now() - timedelta(days=1)
        ),
        Task(
            title="Coffee with Bob",
            description="Casual networking",
            status="Pending",
            priority="Low",
            due_date=datetime.now() + timedelta(days=14)
        )
    ]

    # Link tasks to profiles
    tasks[0].profiles.append(sample_profiles[0])
    tasks[1].profiles.append(sample_profiles[1])
    tasks[2].profiles.append(sample_profiles[2])
    tasks[3].profiles.append(sample_profiles[3])

    for task in tasks:
        test_db.add(task)

    test_db.commit()

    return tasks


@pytest.fixture
def sample_goals(test_db, sample_tasks, sample_profiles):
    """Create sample goals for testing"""
    goals = [
        Goal(
            title="Expand Tech Partnerships",
            description="Build 5 new partnerships in tech sector",
            target_date=None,
            progress=40,
            status="Active"
        ),
        Goal(
            title="Executive Network Growth",
            description="Connect with 10 C-level executives",
            target_date=None,
            progress=70,
            status="Active"
        ),
        Goal(
            title="Design Collaboration",
            description="Complete 3 design projects",
            target_date=None,
            progress=100,
            status="Achieved"
        )
    ]

    # Link goals to tasks and profiles
    goals[0].tasks.append(sample_tasks[0])
    goals[0].profiles.append(sample_profiles[0])

    goals[1].tasks.append(sample_tasks[1])
    goals[1].profiles.append(sample_profiles[1])

    goals[2].tasks.append(sample_tasks[2])
    goals[2].profiles.append(sample_profiles[2])

    for goal in goals:
        test_db.add(goal)

    test_db.commit()

    return goals


@pytest.fixture
def sample_reminders(test_db, sample_profiles):
    """Create sample reminders for testing"""
    from datetime import datetime, timedelta

    reminders = [
        Reminder(
            title="Call John about partnership",
            due_date=datetime.now() + timedelta(days=1),
            priority="High",
            recurring="Weekly",
            profile_id=sample_profiles[0].id
        ),
        Reminder(
            title="Email Jane quarterly report",
            due_date=datetime.now() + timedelta(days=7),
            priority="Medium",
            recurring="Monthly",
            profile_id=sample_profiles[1].id
        ),
        Reminder(
            title="Review Alice's portfolio",
            due_date=datetime.now() - timedelta(days=1),  # Overdue
            priority="High",
            profile_id=sample_profiles[2].id
        )
    ]

    for reminder in reminders:
        test_db.add(reminder)

    test_db.commit()

    return reminders


@pytest.fixture
def sample_relationships(test_db, sample_profiles, sample_companies):
    """Create sample relationships for testing"""
    profile_rels = [
        ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[1].id,
            relationship_type="Colleague",
            bidirectional=True,
            status="Good"
        ),
        ProfileRelationship(
            profile_id=sample_profiles[0].id,
            related_profile_id=sample_profiles[2].id,
            relationship_type="Mentor",
            bidirectional=False,
            status="Good"
        ),
        ProfileRelationship(
            profile_id=sample_profiles[2].id,
            related_profile_id=sample_profiles[3].id,
            relationship_type="Friend",
            bidirectional=True,
            status="Good"
        )
    ]

    company_rels = [
        CompanyRelationship(
            company_id=sample_companies[0].id,
            related_company_id=sample_companies[1].id,
            relationship_type="Partner",
            bidirectional=True,
            status="Good"
        ),
        CompanyRelationship(
            company_id=sample_companies[0].id,
            related_company_id=sample_companies[2].id,
            relationship_type="Client",
            bidirectional=False,
            status="Good"
        )
    ]

    for rel in profile_rels + company_rels:
        test_db.add(rel)

    test_db.commit()

    return {'profiles': profile_rels, 'companies': company_rels}


@pytest.fixture
def sample_interactions(test_db, sample_profiles):
    """Create sample interactions for testing"""
    from datetime import datetime, timedelta

    interactions = [
        Interaction(
            profile_id=sample_profiles[0].id,
            type="Meeting",
            date=datetime.now() - timedelta(days=5),
            notes="Discussed Q4 strategy and partnership opportunities",
            outcome="Positive"
        ),
        Interaction(
            profile_id=sample_profiles[1].id,
            type="Email",
            date=datetime.now() - timedelta(days=2),
            notes="Sent quarterly report and metrics",
            outcome="Pending"
        ),
        Interaction(
            profile_id=sample_profiles[2].id,
            type="Call",
            date=datetime.now() - timedelta(days=10),
            notes="Quick check-in on design project progress",
            outcome="Positive"
        )
    ]

    for interaction in interactions:
        test_db.add(interaction)

    test_db.commit()

    return interactions


@pytest.fixture
def mock_console():
    """Mock Rich console for testing output"""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_questionary():
    """Mock questionary for testing user input"""
    from unittest.mock import Mock, MagicMock

    mock = MagicMock()

    # Common questionary patterns
    mock.text.return_value.ask.return_value = "test input"
    mock.select.return_value.ask.return_value = "test selection"
    mock.confirm.return_value.ask.return_value = True
    mock.press_any_key_to_continue.return_value.ask.return_value = None

    return mock
