"""
Unit tests for Reminder model — all CRUD operations and every attribute
"""

import pytest
from datetime import datetime, timedelta
from leadsauce.models.reminder import Reminder
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company


REMINDER_CATEGORIES = ["call", "email", "meeting", "follow-up", "birthday", "general"]
REMINDER_PRIORITIES = ["low", "medium", "high"]
RECURRENCE_PATTERNS = ["daily", "weekly", "monthly", "yearly"]


class TestReminderCreate:

    def test_create_minimal_reminder_for_profile(self, test_db, sample_profiles):
        reminder = Reminder(
            title="Call John",
            reminder_date=datetime.now() + timedelta(days=1),
            profile_id=sample_profiles[0].id
        )
        test_db.add(reminder)
        test_db.commit()

        assert reminder.id is not None
        assert reminder.title == "Call John"
        assert reminder.profile_id == sample_profiles[0].id
        assert reminder.priority == "medium"
        assert reminder.category == "general"
        assert reminder.completed is False
        assert reminder.completed_at is None
        assert reminder.completion_note is None
        assert reminder.notification_sent is False
        assert reminder.is_recurring is False
        assert reminder.recurrence_pattern is None
        assert reminder.created_at is not None

    def test_create_full_reminder_all_fields(self, test_db, sample_profiles):
        due = datetime.now() + timedelta(days=3)
        reminder = Reminder(
            title="Quarterly review meeting",
            message="Prepare agenda and financials beforehand",
            reminder_date=due,
            priority="high",
            category="meeting",
            profile_id=sample_profiles[0].id,
            is_recurring=True,
            recurrence_pattern="monthly"
        )
        test_db.add(reminder)
        test_db.commit()

        assert reminder.title == "Quarterly review meeting"
        assert reminder.message == "Prepare agenda and financials beforehand"
        assert reminder.priority == "high"
        assert reminder.category == "meeting"
        assert reminder.is_recurring is True
        assert reminder.recurrence_pattern == "monthly"
        assert reminder.profile_id == sample_profiles[0].id

    def test_create_reminder_for_company(self, test_db, sample_companies):
        reminder = Reminder(
            title="Follow up with TechCorp",
            reminder_date=datetime.now() + timedelta(days=7),
            company_id=sample_companies[0].id
        )
        test_db.add(reminder)
        test_db.commit()
        assert reminder.company_id == sample_companies[0].id
        assert reminder.profile_id is None

    def test_create_all_categories(self, test_db, sample_profiles):
        for category in REMINDER_CATEGORIES:
            r = Reminder(
                title=f"Reminder {category}",
                reminder_date=datetime.now() + timedelta(days=1),
                category=category,
                profile_id=sample_profiles[0].id
            )
            test_db.add(r)
        test_db.commit()
        stored = [r.category for r in test_db.query(Reminder).all()]
        for category in REMINDER_CATEGORIES:
            assert category in stored

    def test_create_all_priorities(self, test_db, sample_profiles):
        for priority in REMINDER_PRIORITIES:
            r = Reminder(
                title=f"Reminder {priority}",
                reminder_date=datetime.now() + timedelta(days=1),
                priority=priority,
                profile_id=sample_profiles[0].id
            )
            test_db.add(r)
        test_db.commit()
        for priority in REMINDER_PRIORITIES:
            assert test_db.query(Reminder).filter_by(priority=priority).first() is not None

    def test_create_all_recurrence_patterns(self, test_db, sample_profiles):
        for pattern in RECURRENCE_PATTERNS:
            r = Reminder(
                title=f"Recurring {pattern}",
                reminder_date=datetime.now() + timedelta(days=1),
                is_recurring=True,
                recurrence_pattern=pattern,
                profile_id=sample_profiles[0].id
            )
            test_db.add(r)
        test_db.commit()
        for pattern in RECURRENCE_PATTERNS:
            assert test_db.query(Reminder).filter_by(recurrence_pattern=pattern).first() is not None

    def test_create_non_recurring_reminder(self, test_db, sample_profiles):
        r = Reminder(
            title="One-time reminder",
            reminder_date=datetime.now() + timedelta(days=1),
            is_recurring=False,
            profile_id=sample_profiles[0].id
        )
        test_db.add(r)
        test_db.commit()
        assert r.is_recurring is False
        assert r.recurrence_pattern is None


class TestReminderRead:

    def test_read_by_id(self, test_db, sample_reminders):
        r = test_db.query(Reminder).filter_by(id=sample_reminders[0].id).first()
        assert r is not None
        assert r.title == "Call John about partnership"

    def test_read_all(self, test_db, sample_reminders):
        assert test_db.query(Reminder).count() == 4

    def test_read_by_profile(self, test_db, sample_reminders, sample_profiles):
        rels = test_db.query(Reminder).filter_by(profile_id=sample_profiles[0].id).all()
        assert len(rels) == 1

    def test_read_by_company(self, test_db, sample_reminders, sample_companies):
        rels = test_db.query(Reminder).filter_by(company_id=sample_companies[0].id).all()
        assert len(rels) == 1

    def test_read_by_priority_high(self, test_db, sample_reminders):
        high = test_db.query(Reminder).filter_by(priority="high").all()
        assert len(high) == 2

    def test_read_by_category_call(self, test_db, sample_reminders):
        calls = test_db.query(Reminder).filter_by(category="call").all()
        assert len(calls) == 1

    def test_read_recurring_reminders(self, test_db, sample_reminders):
        recurring = test_db.query(Reminder).filter_by(is_recurring=True).all()
        assert len(recurring) == 2

    def test_read_overdue_reminders(self, test_db, sample_reminders):
        now = datetime.now()
        overdue = test_db.query(Reminder).filter(
            Reminder.reminder_date < now,
            Reminder.completed == False
        ).all()
        assert len(overdue) == 1

    def test_read_incomplete_reminders(self, test_db, sample_reminders):
        incomplete = test_db.query(Reminder).filter_by(completed=False).all()
        assert len(incomplete) == 4


class TestReminderUpdate:

    def test_update_title(self, test_db, sample_reminders):
        r = sample_reminders[0]
        r.title = "Updated reminder title"
        test_db.commit()
        assert test_db.query(Reminder).filter_by(id=r.id).first().title == "Updated reminder title"

    def test_update_message(self, test_db, sample_reminders):
        r = sample_reminders[0]
        r.message = "New message content"
        test_db.commit()
        assert test_db.query(Reminder).filter_by(id=r.id).first().message == "New message content"

    def test_update_reminder_date(self, test_db, sample_reminders):
        r = sample_reminders[0]
        new_date = datetime.now() + timedelta(days=14)
        r.reminder_date = new_date
        test_db.commit()
        refreshed = test_db.query(Reminder).filter_by(id=r.id).first()
        assert abs((refreshed.reminder_date - new_date).total_seconds()) < 2

    def test_update_priority(self, test_db, sample_reminders):
        r = sample_reminders[1]
        r.priority = "high"
        test_db.commit()
        assert test_db.query(Reminder).filter_by(id=r.id).first().priority == "high"

    def test_update_category(self, test_db, sample_reminders):
        r = sample_reminders[0]
        r.category = "meeting"
        test_db.commit()
        assert test_db.query(Reminder).filter_by(id=r.id).first().category == "meeting"

    def test_complete_reminder(self, test_db, sample_reminders):
        r = sample_reminders[0]
        r.complete(note="Called and discussed partnership")
        test_db.commit()
        refreshed = test_db.query(Reminder).filter_by(id=r.id).first()
        assert refreshed.completed is True
        assert refreshed.completed_at is not None
        assert refreshed.completion_note == "Called and discussed partnership"

    def test_complete_reminder_without_note(self, test_db, sample_reminders):
        r = sample_reminders[1]
        r.complete()
        test_db.commit()
        refreshed = test_db.query(Reminder).filter_by(id=r.id).first()
        assert refreshed.completed is True
        assert refreshed.completed_at is not None
        assert refreshed.completion_note is None

    def test_mark_notification_sent(self, test_db, sample_reminders):
        r = sample_reminders[0]
        r.notification_sent = True
        test_db.commit()
        assert test_db.query(Reminder).filter_by(id=r.id).first().notification_sent is True

    def test_enable_recurrence(self, test_db, sample_reminders):
        r = sample_reminders[2]
        r.is_recurring = True
        r.recurrence_pattern = "weekly"
        test_db.commit()
        refreshed = test_db.query(Reminder).filter_by(id=r.id).first()
        assert refreshed.is_recurring is True
        assert refreshed.recurrence_pattern == "weekly"


class TestReminderDelete:

    def test_delete_reminder(self, test_db, sample_reminders):
        rid = sample_reminders[0].id
        test_db.delete(sample_reminders[0])
        test_db.commit()
        assert test_db.query(Reminder).filter_by(id=rid).first() is None

    def test_delete_reminder_preserves_profile(self, test_db, sample_reminders, sample_profiles):
        r = sample_reminders[0]
        pid = r.profile_id
        test_db.delete(r)
        test_db.commit()
        assert test_db.query(Profile).filter_by(id=pid).first() is not None

    def test_delete_profile_cascades_reminders(self, test_db, sample_reminders, sample_profiles):
        profile = sample_profiles[0]
        pid = profile.id
        test_db.delete(profile)
        test_db.commit()
        remaining = test_db.query(Reminder).filter_by(profile_id=pid).all()
        assert len(remaining) == 0

    def test_delete_company_cascades_reminders(self, test_db, sample_reminders, sample_companies):
        company = sample_companies[0]
        cid = company.id
        test_db.delete(company)
        test_db.commit()
        remaining = test_db.query(Reminder).filter_by(company_id=cid).all()
        assert len(remaining) == 0


class TestReminderIsOverdue:

    def test_overdue_incomplete_reminder(self, test_db, sample_profiles):
        r = Reminder(
            title="Overdue",
            reminder_date=datetime.now() - timedelta(days=1),
            profile_id=sample_profiles[0].id
        )
        test_db.add(r)
        test_db.commit()
        assert r.is_overdue() is True

    def test_future_reminder_not_overdue(self, test_db, sample_profiles):
        r = Reminder(
            title="Future",
            reminder_date=datetime.now() + timedelta(days=7),
            profile_id=sample_profiles[0].id
        )
        test_db.add(r)
        test_db.commit()
        assert r.is_overdue() is False

    def test_completed_reminder_not_overdue(self, test_db, sample_profiles):
        r = Reminder(
            title="Completed",
            reminder_date=datetime.now() - timedelta(days=2),
            profile_id=sample_profiles[0].id
        )
        test_db.add(r)
        test_db.commit()
        r.complete()
        test_db.commit()
        assert r.is_overdue() is False


class TestReminderGetLinkedEntityInfo:

    def test_linked_to_profile(self, test_db, sample_reminders, sample_profiles):
        r = sample_reminders[0]
        entity_type, entity_name, entity_id = r.get_linked_entity_info()
        assert entity_type == "profile"
        assert entity_id == sample_profiles[0].id

    def test_linked_to_company(self, test_db, sample_reminders, sample_companies):
        r = sample_reminders[3]
        entity_type, entity_name, entity_id = r.get_linked_entity_info()
        assert entity_type == "company"
        assert entity_id == sample_companies[0].id

    def test_reminder_to_dict(self, test_db, sample_reminders):
        d = sample_reminders[0].to_dict()
        assert 'title' in d
        assert 'priority' in d
        assert 'category' in d
        assert 'completed' in d
        assert 'is_recurring' in d
