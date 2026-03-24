"""
End-to-end tests simulating full user flows through the TUI.

Each test represents a complete user journey:
  - Add a record with all fields
  - Verify it was saved
  - Edit/update it
  - Verify the update
  - Delete/complete it
  - Verify cleanup
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag
from leadsauce.models.task import Task
from leadsauce.models.goal import Goal
from leadsauce.models.reminder import Reminder
from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship


# ============================================================================
# PROFILE E2E FLOWS
# ============================================================================

class TestProfileE2EFlow:
    """Full CRUD flow: Add → View → Edit → Delete"""

    def test_add_profile_minimal(self, test_db):
        """E2E: User adds a profile with only required fields"""
        # Step 1: Add
        profile = Profile(name="New Contact", seniority="Junior")
        test_db.add(profile)
        test_db.commit()

        # Step 2: Verify created
        saved = test_db.query(Profile).filter_by(name="New Contact").first()
        assert saved is not None
        assert saved.id is not None
        assert saved.seniority == "Junior"

        # Step 3: Edit
        saved.email = "new.contact@example.com"
        saved.phone = "+1112223333"
        test_db.commit()

        # Step 4: Verify edit
        updated = test_db.query(Profile).filter_by(id=saved.id).first()
        assert updated.email == "new.contact@example.com"
        assert updated.phone == "+1112223333"

        # Step 5: Delete
        test_db.delete(updated)
        test_db.commit()
        assert test_db.query(Profile).filter_by(name="New Contact").first() is None

    def test_add_profile_all_fields(self, test_db, sample_companies, sample_tags):
        """E2E: User adds a fully-populated profile"""
        profile = Profile(
            name="Full Profile User",
            email="full@example.com",
            phone="+9998887777",
            seniority="Senior",
            company_id=sample_companies[0].id,
            generation="Gen X",
            married=True,
            has_children=True,
            ie_score=70,
            is_score=65,
            good_at="Python, Leadership, Negotiation",
            need_to_work="Patience, Delegation",
            work_for="Financial independence",
            additional_info="Referred by John Doe",
            notes="Key decision maker at TechCorp"
        )
        profile.tags.append(sample_tags[0])
        profile.tags.append(sample_tags[2])
        test_db.add(profile)
        test_db.commit()

        # Verify all fields
        saved = test_db.query(Profile).filter_by(email="full@example.com").first()
        assert saved.name == "Full Profile User"
        assert saved.phone == "+9998887777"
        assert saved.seniority == "Senior"
        assert saved.company_id == sample_companies[0].id
        assert saved.generation == "Gen X"
        assert saved.married is True
        assert saved.has_children is True
        assert saved.ie_score == 70
        assert saved.is_score == 65
        assert saved.good_at == "Python, Leadership, Negotiation"
        assert saved.need_to_work == "Patience, Delegation"
        assert saved.work_for == "Financial independence"
        assert saved.additional_info == "Referred by John Doe"
        assert saved.notes == "Key decision maker at TechCorp"
        assert len(saved.tags) == 2

    def test_edit_profile_company(self, test_db, sample_profiles, sample_companies):
        """E2E: User reassigns a profile to a different company"""
        profile = sample_profiles[3]  # Bob Wilson at FinanceGlobal
        original_company_id = profile.company_id

        profile.company_id = sample_companies[0].id  # Move to TechCorp
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert updated.company_id == sample_companies[0].id
        assert updated.company_id != original_company_id

    def test_add_and_remove_tags_from_profile(self, test_db, sample_profiles, sample_tags):
        """E2E: User adds then removes tags from a profile"""
        profile = sample_profiles[3]  # Bob Wilson has 1 tag
        assert len(profile.tags) == 1

        # Add a tag
        profile.tags.append(sample_tags[2])
        test_db.commit()
        assert len(test_db.query(Profile).filter_by(id=profile.id).first().tags) == 2

        # Remove original tag
        profile.tags.remove(sample_tags[3])
        test_db.commit()
        refreshed = test_db.query(Profile).filter_by(id=profile.id).first()
        assert len(refreshed.tags) == 1
        assert "Partner" in [t.name for t in refreshed.tags]

    def test_profile_interaction_tracking(self, test_db, sample_profiles):
        """E2E: User logs contact with a profile"""
        from leadsauce.models.interaction import Interaction
        profile = sample_profiles[0]

        interaction = Interaction(
            profile_id=profile.id,
            interaction_type="call",
            notes="Discussed Q4 strategy"
        )
        test_db.add(interaction)
        test_db.commit()
        test_db.refresh(profile)

        profile.update_last_contact()
        test_db.commit()

        updated = test_db.query(Profile).filter_by(id=profile.id).first()
        assert updated.last_contact is not None
        assert updated.interaction_count == 1

    def test_search_and_view_profile(self, test_db, sample_profiles):
        """E2E: User searches for a profile by name and views details"""
        results = test_db.query(Profile).filter(Profile.name.ilike("%john%")).all()
        assert len(results) >= 1

        profile = results[0]
        detail = profile.to_dict(include_relations=True)
        assert 'name' in detail
        assert 'email' in detail
        assert 'seniority' in detail


# ============================================================================
# COMPANY E2E FLOWS
# ============================================================================

class TestCompanyE2EFlow:

    def test_add_company_full_flow(self, test_db):
        """E2E: Add → View → Edit → Delete company"""
        # Add
        company = Company(
            name="E2E Corp",
            industry="Technology",
            size="100-500",
            location="Austin, TX",
            website="https://e2ecorp.example.com",
            notes="Test company for E2E"
        )
        test_db.add(company)
        test_db.commit()

        # Verify
        saved = test_db.query(Company).filter_by(name="E2E Corp").first()
        assert saved is not None
        assert saved.industry == "Technology"
        assert saved.size == "100-500"
        assert saved.location == "Austin, TX"
        assert saved.website == "https://e2ecorp.example.com"
        assert saved.notes == "Test company for E2E"

        # Edit
        saved.industry = "FinTech"
        saved.size = "500-1000"
        test_db.commit()
        updated = test_db.query(Company).filter_by(id=saved.id).first()
        assert updated.industry == "FinTech"
        assert updated.size == "500-1000"

        # Delete
        test_db.delete(updated)
        test_db.commit()
        assert test_db.query(Company).filter_by(name="E2E Corp").first() is None

    def test_view_company_with_profiles(self, test_db, sample_profiles, sample_companies):
        """E2E: User views a company and sees linked profiles"""
        company = test_db.query(Company).filter_by(id=sample_companies[0].id).first()
        assert len(company.profiles) == 2
        profile_names = [p.name for p in company.profiles]
        assert "John Doe" in profile_names
        assert "Jane Smith" in profile_names

    def test_delete_company_nullifies_profiles(self, test_db, sample_profiles, sample_companies):
        """E2E: Deleting a company sets profile.company_id to NULL"""
        company = sample_companies[0]
        profile_ids = [p.id for p in company.profiles]

        test_db.delete(company)
        test_db.commit()

        for pid in profile_ids:
            p = test_db.query(Profile).filter_by(id=pid).first()
            assert p is not None
            assert p.company_id is None


# ============================================================================
# TAG E2E FLOWS
# ============================================================================

class TestTagE2EFlow:

    def test_add_tag_full_flow(self, test_db, sample_profiles):
        """E2E: Add tag → assign to profile → view count → delete"""
        # Add tag
        tag = Tag(name="E2E Test Tag", color="#123456", description="Created in E2E test")
        test_db.add(tag)
        test_db.commit()

        # Assign to profiles
        sample_profiles[0].tags.append(tag)
        sample_profiles[1].tags.append(tag)
        test_db.commit()

        # Verify count
        saved_tag = test_db.query(Tag).filter_by(name="E2E Test Tag").first()
        assert len(saved_tag.profiles) == 2

        # Edit
        saved_tag.name = "E2E Updated Tag"
        saved_tag.color = "#654321"
        test_db.commit()
        updated = test_db.query(Tag).filter_by(id=saved_tag.id).first()
        assert updated.name == "E2E Updated Tag"
        assert updated.color == "#654321"

        # Delete (profiles should be preserved)
        test_db.delete(updated)
        test_db.commit()
        assert test_db.query(Tag).filter_by(name="E2E Updated Tag").first() is None
        assert test_db.query(Profile).filter_by(id=sample_profiles[0].id).first() is not None


# ============================================================================
# TASK E2E FLOWS
# ============================================================================

class TestTaskE2EFlow:

    def test_create_task_full_flow(self, test_db, sample_profiles, sample_companies, sample_tags):
        """E2E: Create task with all fields → link entities → complete it"""
        # Create
        task = Task(
            title="Prepare Q4 Partnership Proposal",
            description="Draft a comprehensive proposal covering tech integration and revenue sharing",
            status="pending",
            priority="high",
            due_date=datetime.now() + timedelta(days=5)
        )
        task.profiles.append(sample_profiles[0])
        task.companies.append(sample_companies[0])
        task.tags.append(sample_tags[0])
        test_db.add(task)
        test_db.commit()

        # Verify creation
        saved = test_db.query(Task).filter_by(title="Prepare Q4 Partnership Proposal").first()
        assert saved is not None
        assert saved.status == "pending"
        assert saved.priority == "high"
        assert len(saved.profiles) == 1
        assert len(saved.companies) == 1
        assert len(saved.tags) == 1

        # Update to in_progress
        saved.update_status("in_progress")
        test_db.commit()
        assert test_db.query(Task).filter_by(id=saved.id).first().status == "in_progress"

        # Complete
        saved.complete()
        test_db.commit()
        completed = test_db.query(Task).filter_by(id=saved.id).first()
        assert completed.status == "completed"
        assert completed.completed_at is not None

    def test_create_task_with_all_priorities(self, test_db):
        """E2E: Create tasks at each priority level and filter"""
        priorities = {"low": "Low priority item", "medium": "Medium task",
                      "high": "High priority action", "urgent": "URGENT: Critical fix"}
        for priority, title in priorities.items():
            t = Task(title=title, priority=priority)
            test_db.add(t)
        test_db.commit()

        for priority in priorities:
            t = test_db.query(Task).filter_by(priority=priority).first()
            assert t is not None

    def test_filter_overdue_tasks(self, test_db, sample_tasks):
        """E2E: User filters to see overdue tasks"""
        now = datetime.now()
        overdue = test_db.query(Task).filter(
            Task.due_date < now,
            Task.status.notin_(["completed", "cancelled"])
        ).all()
        assert len(overdue) >= 1
        for task in overdue:
            assert task.due_date < now
            assert task.status not in ["completed", "cancelled"]

    def test_link_multiple_profiles_to_task(self, test_db, sample_profiles):
        """E2E: User links multiple profiles to a single task"""
        task = Task(title="Team meeting prep")
        for profile in sample_profiles:
            task.profiles.append(profile)
        test_db.add(task)
        test_db.commit()

        saved = test_db.query(Task).filter_by(title="Team meeting prep").first()
        assert len(saved.profiles) == len(sample_profiles)

    def test_cancel_task(self, test_db):
        """E2E: User cancels a task"""
        task = Task(title="Cancelled task", status="pending")
        test_db.add(task)
        test_db.commit()

        task.update_status("cancelled")
        test_db.commit()

        updated = test_db.query(Task).filter_by(id=task.id).first()
        assert updated.status == "cancelled"
        assert updated.is_overdue() is False

    def test_update_task_due_date(self, test_db, sample_tasks):
        """E2E: User reschedules a task"""
        task = sample_tasks[0]
        new_due = datetime.now() + timedelta(days=14)
        task.due_date = new_due
        test_db.commit()
        refreshed = test_db.query(Task).filter_by(id=task.id).first()
        assert abs((refreshed.due_date - new_due).total_seconds()) < 2


# ============================================================================
# GOAL E2E FLOWS
# ============================================================================

class TestGoalE2EFlow:

    def test_create_goal_full_flow(self, test_db, sample_profiles, sample_companies, sample_tags):
        """E2E: Create goal → link entities → track progress → complete"""
        # Create tasks
        t1 = Task(title="Goal task 1", status="pending")
        t2 = Task(title="Goal task 2", status="pending")
        t3 = Task(title="Goal task 3", status="pending")
        test_db.add_all([t1, t2, t3])
        test_db.commit()

        # Create goal with all fields
        goal = Goal(
            title="Build 3 Tech Partnerships",
            description="Establish partnerships with 3 tech companies by end of Q4",
            status="active",
            priority="high",
            target_date=datetime.now() + timedelta(days=90)
        )
        goal.tasks.extend([t1, t2, t3])
        goal.profiles.append(sample_profiles[0])
        goal.companies.append(sample_companies[0])
        goal.tags.append(sample_tags[0])
        test_db.add(goal)
        test_db.commit()

        # Verify creation
        saved = test_db.query(Goal).filter_by(title="Build 3 Tech Partnerships").first()
        assert saved is not None
        assert len(saved.tasks) == 3
        assert len(saved.profiles) == 1
        assert len(saved.companies) == 1
        assert len(saved.tags) == 1
        assert saved.progress == 0.0

        # Complete first task → update progress
        t1.complete()
        test_db.commit()
        saved.update_progress()
        test_db.commit()
        assert abs(saved.progress - 33.33) < 0.5

        # Complete second task
        t2.complete()
        test_db.commit()
        saved.update_progress()
        test_db.commit()
        assert abs(saved.progress - 66.67) < 0.5

        # Complete all tasks → goal auto-completes
        t3.complete()
        test_db.commit()
        saved.update_progress()
        test_db.commit()
        assert saved.status == "completed"
        assert saved.progress == 100.0
        assert saved.completed_at is not None

    def test_goal_without_tasks_manual_progress(self, test_db):
        """E2E: User manually updates progress on a goal with no tasks"""
        goal = Goal(title="Networking goal - no tasks", status="active", priority="medium")
        test_db.add(goal)
        test_db.commit()

        assert goal.progress == 0.0
        assert goal.calculate_progress() == 0.0

        goal.progress = 50.0
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=goal.id).first().progress == 50.0

    def test_achieved_goals_view(self, test_db, sample_goals):
        """E2E: User views achieved goals"""
        achieved = test_db.query(Goal).filter_by(status="completed").all()
        assert len(achieved) == 1
        assert achieved[0].title == "Design Collaboration"

    def test_link_and_unlink_profile_from_goal(self, test_db, sample_goals, sample_profiles):
        """E2E: User links a profile then unlinks it"""
        goal = sample_goals[1]
        initial_count = len(goal.profiles)

        goal.profiles.append(sample_profiles[2])
        test_db.commit()
        assert len(test_db.query(Goal).filter_by(id=goal.id).first().profiles) == initial_count + 1

        goal.profiles.remove(sample_profiles[2])
        test_db.commit()
        assert len(test_db.query(Goal).filter_by(id=goal.id).first().profiles) == initial_count

    def test_overdue_goal_detection(self, test_db, sample_goals):
        """E2E: User checks for overdue goals"""
        overdue = [g for g in test_db.query(Goal).all() if g.is_overdue()]
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue Goal"

    def test_delete_goal_preserves_all_linked_entities(self, test_db, sample_goals, sample_profiles, sample_companies, sample_tasks):
        """E2E: Deleting a goal does not affect linked profiles, companies, or tasks"""
        goal = sample_goals[0]
        profile_ids = [p.id for p in goal.profiles]
        company_ids = [c.id for c in goal.companies]
        task_ids = [t.id for t in goal.tasks]

        test_db.delete(goal)
        test_db.commit()

        for pid in profile_ids:
            assert test_db.query(Profile).filter_by(id=pid).first() is not None
        for cid in company_ids:
            assert test_db.query(Company).filter_by(id=cid).first() is not None
        for tid in task_ids:
            assert test_db.query(Task).filter_by(id=tid).first() is not None


# ============================================================================
# RELATIONSHIP E2E FLOWS
# ============================================================================

class TestRelationshipE2EFlow:

    def test_add_profile_relationship_full_flow(self, test_db, sample_profiles):
        """E2E: Add relationship → view network → update → delete"""
        # Add
        rel = ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[3].id,
            relationship_type="Advisor",
            description="John advises Bob on career growth",
            status="Good",
            bidirectional=False
        )
        test_db.add(rel)
        test_db.commit()

        # View
        saved = test_db.query(ProfileRelationship).filter_by(relationship_type="Advisor").first()
        assert saved is not None
        assert saved.from_profile.name == "John Doe"
        assert saved.to_profile.name == "Bob Wilson"
        assert saved.status == "Good"

        # Update
        saved.status = "Bad"
        saved.bidirectional = True
        test_db.commit()
        updated = test_db.query(ProfileRelationship).filter_by(id=saved.id).first()
        assert updated.status == "Bad"
        assert updated.bidirectional is True

        # Delete
        test_db.delete(updated)
        test_db.commit()
        assert test_db.query(ProfileRelationship).filter_by(relationship_type="Advisor").first() is None

    def test_add_company_relationship_full_flow(self, test_db, sample_companies):
        """E2E: Add company relationship → verify → update → delete"""
        rel = CompanyRelationship(
            from_company_id=sample_companies[1].id,
            to_company_id=sample_companies[2].id,
            relationship_type="Investor",
            description="DesignStudio invests in FinanceGlobal",
            status="Good",
            bidirectional=False
        )
        test_db.add(rel)
        test_db.commit()

        saved = test_db.query(CompanyRelationship).filter_by(relationship_type="Investor").first()
        assert saved is not None
        assert saved.from_company.name == "DesignStudio LLC"

        saved.status = "No Interest"
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(id=saved.id).first().status == "No Interest"

        test_db.delete(saved)
        test_db.commit()
        assert test_db.query(CompanyRelationship).filter_by(relationship_type="Investor").first() is None

    def test_network_query_all_connections(self, test_db, sample_profile_relationships, sample_profiles):
        """E2E: User views all network connections for a profile"""
        pid = sample_profiles[0].id
        connections = test_db.query(ProfileRelationship).filter(
            (ProfileRelationship.from_profile_id == pid) |
            (ProfileRelationship.to_profile_id == pid)
        ).all()
        assert len(connections) == 2

    def test_filter_relationships_by_status(self, test_db, sample_profile_relationships):
        """E2E: User filters relationships by status"""
        good = test_db.query(ProfileRelationship).filter_by(status="Good").all()
        bad = test_db.query(ProfileRelationship).filter_by(status="Bad").all()
        no_interest = test_db.query(ProfileRelationship).filter_by(status="No Interest").all()

        assert len(good) == 3
        assert len(bad) == 0
        assert len(no_interest) == 1


# ============================================================================
# REMINDER E2E FLOWS
# ============================================================================

class TestReminderE2EFlow:

    def test_add_reminder_full_flow(self, test_db, sample_profiles):
        """E2E: Add reminder → view → complete → verify"""
        # Add
        reminder = Reminder(
            title="Call John about Q4 strategy",
            message="Prepare talking points beforehand",
            reminder_date=datetime.now() + timedelta(days=2),
            priority="high",
            category="call",
            profile_id=sample_profiles[0].id,
            is_recurring=True,
            recurrence_pattern="weekly"
        )
        test_db.add(reminder)
        test_db.commit()

        # Verify saved
        saved = test_db.query(Reminder).filter_by(title="Call John about Q4 strategy").first()
        assert saved is not None
        assert saved.priority == "high"
        assert saved.category == "call"
        assert saved.is_recurring is True
        assert saved.recurrence_pattern == "weekly"
        assert saved.completed is False

        # Complete
        saved.complete(note="Called, discussed Q4 plan, follow-up in 2 weeks")
        test_db.commit()
        completed = test_db.query(Reminder).filter_by(id=saved.id).first()
        assert completed.completed is True
        assert completed.completed_at is not None
        assert "Called" in completed.completion_note

    def test_overdue_reminder_detection(self, test_db, sample_reminders):
        """E2E: User views overdue reminders"""
        overdue = [r for r in test_db.query(Reminder).all() if r.is_overdue()]
        assert len(overdue) == 1

    def test_reminder_linked_to_company(self, test_db, sample_companies):
        """E2E: Create a company-linked reminder"""
        reminder = Reminder(
            title="Follow up with TechCorp about contract",
            reminder_date=datetime.now() + timedelta(days=5),
            priority="medium",
            category="follow-up",
            company_id=sample_companies[0].id
        )
        test_db.add(reminder)
        test_db.commit()

        entity_type, entity_name, entity_id = reminder.get_linked_entity_info()
        assert entity_type == "company"
        assert entity_id == sample_companies[0].id


# ============================================================================
# CROSS-FEATURE E2E FLOWS
# ============================================================================

class TestCrossFeatureE2EFlow:

    def test_full_contact_management_flow(self, test_db):
        """E2E: Add company → add profile at company → tag profile → create task → create goal → complete"""
        # 1. Create company
        company = Company(name="Acme Corp", industry="Manufacturing", size="500-1000")
        test_db.add(company)
        test_db.commit()

        # 2. Create profile at that company
        profile = Profile(
            name="Alice Brown",
            email="alice.brown@acme.example.com",
            seniority="Senior",
            company_id=company.id,
            generation="Millennial",
            good_at="Operations, Supply Chain"
        )
        test_db.add(profile)
        test_db.commit()

        # 3. Tag the profile
        tag = Tag(name="Operations", color="#FF8800")
        test_db.add(tag)
        test_db.commit()
        profile.tags.append(tag)
        test_db.commit()

        # 4. Create a task linked to profile
        task = Task(
            title="Send supply chain proposal to Alice",
            priority="high",
            due_date=datetime.now() + timedelta(days=7)
        )
        task.profiles.append(profile)
        task.companies.append(company)
        test_db.add(task)
        test_db.commit()

        # 5. Create a goal linking it all
        goal = Goal(
            title="Close Acme Corp deal",
            description="Sign partnership agreement with Acme Corp",
            priority="high",
            target_date=datetime.now() + timedelta(days=30)
        )
        goal.tasks.append(task)
        goal.profiles.append(profile)
        goal.companies.append(company)
        test_db.add(goal)
        test_db.commit()

        # 6. Verify everything is linked
        saved_goal = test_db.query(Goal).filter_by(title="Close Acme Corp deal").first()
        assert len(saved_goal.tasks) == 1
        assert len(saved_goal.profiles) == 1
        assert len(saved_goal.companies) == 1

        # 7. Complete the task
        task.complete()
        test_db.commit()
        saved_goal.update_progress()
        test_db.commit()
        assert saved_goal.status == "completed"
        assert saved_goal.progress == 100.0

    def test_network_relationship_with_goals(self, test_db, sample_profiles, sample_companies):
        """E2E: Create relationship between profiles, then create shared goal"""
        # Add relationship
        rel = ProfileRelationship(
            from_profile_id=sample_profiles[0].id,
            to_profile_id=sample_profiles[1].id,
            relationship_type="Business Partner",
            bidirectional=True,
            status="Good"
        )
        test_db.add(rel)
        test_db.commit()

        # Create shared goal for both contacts
        goal = Goal(title="Joint partnership initiative")
        goal.profiles.append(sample_profiles[0])
        goal.profiles.append(sample_profiles[1])
        test_db.add(goal)
        test_db.commit()

        saved = test_db.query(Goal).filter_by(title="Joint partnership initiative").first()
        assert len(saved.profiles) == 2

    def test_dashboard_statistics(self, test_db, sample_profiles, sample_companies, sample_tags, sample_tasks, sample_goals):
        """E2E: Verify counts that would appear on dashboard"""
        profile_count = test_db.query(Profile).count()
        company_count = test_db.query(Company).count()
        tag_count = test_db.query(Tag).count()
        task_count = test_db.query(Task).count()
        pending_tasks = test_db.query(Task).filter_by(status="pending").count()
        active_goals = test_db.query(Goal).filter_by(status="active").count()

        assert profile_count == 4
        assert company_count == 3
        assert tag_count == 4
        assert task_count == 5
        assert pending_tasks >= 2
        assert active_goals == 3

    def test_search_across_profiles(self, test_db, sample_profiles, sample_companies, sample_tags):
        """E2E: User searches for contacts and gets correct results"""
        # Search by name
        by_name = test_db.query(Profile).filter(Profile.name.ilike("%alice%")).all()
        assert len(by_name) == 1

        # Search by email domain
        by_email = test_db.query(Profile).filter(Profile.email.ilike("%@example.com%")).all()
        assert len(by_email) == 4

        # Search by skills
        by_skills = test_db.query(Profile).filter(Profile.good_at.ilike("%design%")).all()
        assert len(by_skills) == 1
        assert by_skills[0].name == "Alice Johnson"

        # Search by generation
        gen_z = test_db.query(Profile).filter_by(generation="Gen Z").all()
        assert len(gen_z) == 1
        assert gen_z[0].name == "Bob Wilson"

    def test_pagination_profile_list(self, test_db):
        """E2E: User browses paginated profile list"""
        PAGE_SIZE = 20

        # Create 25 profiles
        for i in range(25):
            p = Profile(name=f"User {i:03d}", seniority="Junior")
            test_db.add(p)
        test_db.commit()

        total = test_db.query(Profile).count()
        assert total == 25

        # Page 1
        page1 = test_db.query(Profile).order_by(Profile.name).limit(PAGE_SIZE).offset(0).all()
        assert len(page1) == PAGE_SIZE

        # Page 2
        page2 = test_db.query(Profile).order_by(Profile.name).limit(PAGE_SIZE).offset(PAGE_SIZE).all()
        assert len(page2) == 5

        # No overlap
        ids_page1 = {p.id for p in page1}
        ids_page2 = {p.id for p in page2}
        assert ids_page1.isdisjoint(ids_page2)
