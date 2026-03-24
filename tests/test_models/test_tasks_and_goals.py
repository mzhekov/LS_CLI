"""
Unit tests for Task and Goal models — all CRUD operations and every attribute
"""

import pytest
from datetime import datetime, timedelta
from leadsauce.models.task import Task
from leadsauce.models.goal import Goal
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag


# ============================================================================
# TASK TESTS
# ============================================================================

class TestTaskCreate:
    """Test Task creation covering every field"""

    def test_create_minimal_task(self, test_db):
        task = Task(title="Follow up call")
        test_db.add(task)
        test_db.commit()

        assert task.id is not None
        assert task.title == "Follow up call"
        assert task.status == "pending"
        assert task.priority == "medium"
        assert task.description is None
        assert task.due_date is None
        assert task.completed_at is None
        assert task.created_at is not None

    def test_create_full_task_all_fields(self, test_db):
        due = datetime.now() + timedelta(days=7)
        task = Task(
            title="Send partnership proposal",
            description="Draft and send Q4 proposal",
            status="in_progress",
            priority="high",
            due_date=due
        )
        test_db.add(task)
        test_db.commit()

        assert task.title == "Send partnership proposal"
        assert task.description == "Draft and send Q4 proposal"
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.due_date is not None

    def test_create_task_all_statuses(self, test_db):
        for status in ["pending", "in_progress", "completed", "cancelled"]:
            t = Task(title=f"Task {status}", status=status)
            test_db.add(t)
        test_db.commit()
        for status in ["pending", "in_progress", "completed", "cancelled"]:
            assert test_db.query(Task).filter_by(status=status).first() is not None

    def test_create_task_all_priorities(self, test_db):
        for priority in ["low", "medium", "high", "urgent"]:
            t = Task(title=f"Task {priority}", priority=priority)
            test_db.add(t)
        test_db.commit()
        for priority in ["low", "medium", "high", "urgent"]:
            assert test_db.query(Task).filter_by(priority=priority).first() is not None

    def test_create_task_with_profile_link(self, test_db, sample_profiles):
        task = Task(title="Profile linked task")
        task.profiles.append(sample_profiles[0])
        test_db.add(task)
        test_db.commit()
        assert len(task.profiles) == 1

    def test_create_task_with_company_link(self, test_db, sample_companies):
        task = Task(title="Company linked task")
        task.companies.append(sample_companies[0])
        test_db.add(task)
        test_db.commit()
        assert len(task.companies) == 1

    def test_create_task_with_tag_link(self, test_db, sample_tags):
        task = Task(title="Tagged task")
        task.tags.append(sample_tags[0])
        task.tags.append(sample_tags[1])
        test_db.add(task)
        test_db.commit()
        assert len(task.tags) == 2

    def test_create_task_with_multiple_profiles(self, test_db, sample_profiles):
        task = Task(title="Multi-profile task")
        task.profiles.extend(sample_profiles[:3])
        test_db.add(task)
        test_db.commit()
        assert len(task.profiles) == 3

    def test_create_task_with_all_links(self, test_db, sample_profiles, sample_companies, sample_tags):
        task = Task(title="Fully linked task", priority="urgent")
        task.profiles.append(sample_profiles[0])
        task.companies.append(sample_companies[0])
        task.tags.append(sample_tags[0])
        test_db.add(task)
        test_db.commit()
        assert len(task.profiles) == 1
        assert len(task.companies) == 1
        assert len(task.tags) == 1

    def test_task_default_status_is_pending(self, test_db):
        task = Task(title="Default status task")
        test_db.add(task)
        test_db.commit()
        assert task.status == "pending"

    def test_task_default_priority_is_medium(self, test_db):
        task = Task(title="Default priority task")
        test_db.add(task)
        test_db.commit()
        assert task.priority == "medium"


class TestTaskRead:
    """Test Task read/query operations"""

    def test_read_by_id(self, test_db, sample_tasks):
        t = test_db.query(Task).filter_by(id=sample_tasks[0].id).first()
        assert t is not None
        assert t.title == "Follow up with John"

    def test_read_all_tasks(self, test_db, sample_tasks):
        assert test_db.query(Task).count() == len(sample_tasks)

    def test_read_by_status_pending(self, test_db, sample_tasks):
        pending = test_db.query(Task).filter_by(status="pending").all()
        assert len(pending) >= 2

    def test_read_by_status_in_progress(self, test_db, sample_tasks):
        assert test_db.query(Task).filter_by(status="in_progress").count() == 1

    def test_read_by_status_completed(self, test_db, sample_tasks):
        assert test_db.query(Task).filter_by(status="completed").count() == 1

    def test_read_by_priority_high(self, test_db, sample_tasks):
        assert test_db.query(Task).filter_by(priority="high").count() == 2

    def test_read_by_priority_urgent(self, test_db, sample_tasks):
        assert test_db.query(Task).filter_by(priority="urgent").count() == 1

    def test_read_overdue_tasks(self, test_db, sample_tasks):
        now = datetime.now()
        overdue = test_db.query(Task).filter(
            Task.due_date < now,
            Task.status.notin_(["completed", "cancelled"])
        ).all()
        assert len(overdue) >= 1

    def test_read_tasks_for_profile(self, test_db, sample_tasks, sample_profiles):
        profile = sample_profiles[0]
        profile_tasks = [t for t in test_db.query(Task).all() if profile in t.profiles]
        assert len(profile_tasks) == 1
        assert profile_tasks[0].title == "Follow up with John"

    def test_read_task_linked_entities(self, test_db, sample_tasks):
        t = test_db.query(Task).filter_by(title="Follow up with John").first()
        assert len(t.profiles) == 1
        assert len(t.companies) == 1
        assert len(t.tags) == 1


class TestTaskUpdate:
    """Test Task update operations"""

    def test_update_title(self, test_db, sample_tasks):
        t = sample_tasks[0]
        t.title = "Updated title"
        test_db.commit()
        assert test_db.query(Task).filter_by(id=t.id).first().title == "Updated title"

    def test_update_description(self, test_db, sample_tasks):
        t = sample_tasks[0]
        t.description = "New description"
        test_db.commit()
        assert test_db.query(Task).filter_by(id=t.id).first().description == "New description"

    def test_update_status_to_in_progress(self, test_db, sample_tasks):
        t = sample_tasks[0]
        t.update_status("in_progress")
        test_db.commit()
        assert test_db.query(Task).filter_by(id=t.id).first().status == "in_progress"

    def test_complete_task(self, test_db, sample_tasks):
        t = sample_tasks[0]
        t.complete()
        test_db.commit()
        refreshed = test_db.query(Task).filter_by(id=t.id).first()
        assert refreshed.status == "completed"
        assert refreshed.completed_at is not None

    def test_cancel_task(self, test_db, sample_tasks):
        t = sample_tasks[0]
        t.update_status("cancelled")
        test_db.commit()
        assert test_db.query(Task).filter_by(id=t.id).first().status == "cancelled"

    def test_update_priority(self, test_db, sample_tasks):
        t = sample_tasks[3]
        t.priority = "urgent"
        test_db.commit()
        assert test_db.query(Task).filter_by(id=t.id).first().priority == "urgent"

    def test_update_due_date(self, test_db, sample_tasks):
        t = sample_tasks[0]
        new_due = datetime.now() + timedelta(days=30)
        t.due_date = new_due
        test_db.commit()
        refreshed = test_db.query(Task).filter_by(id=t.id).first()
        assert abs((refreshed.due_date - new_due).total_seconds()) < 2

    def test_clear_due_date(self, test_db, sample_tasks):
        t = sample_tasks[0]
        t.due_date = None
        test_db.commit()
        assert test_db.query(Task).filter_by(id=t.id).first().due_date is None

    def test_add_profile_to_task(self, test_db, sample_tasks, sample_profiles):
        t = sample_tasks[3]
        initial = len(t.profiles)
        t.profiles.append(sample_profiles[0])
        test_db.commit()
        assert len(test_db.query(Task).filter_by(id=t.id).first().profiles) == initial + 1

    def test_remove_profile_from_task(self, test_db, sample_tasks, sample_profiles):
        t = sample_tasks[0]
        t.profiles.remove(sample_profiles[0])
        test_db.commit()
        assert len(test_db.query(Task).filter_by(id=t.id).first().profiles) == 0

    def test_add_company_to_task(self, test_db, sample_tasks, sample_companies):
        t = sample_tasks[1]
        t.companies.append(sample_companies[1])
        test_db.commit()
        assert len(test_db.query(Task).filter_by(id=t.id).first().companies) >= 1

    def test_add_tag_to_task(self, test_db, sample_tasks, sample_tags):
        t = sample_tasks[1]
        t.tags.append(sample_tags[2])
        test_db.commit()
        assert sample_tags[2] in test_db.query(Task).filter_by(id=t.id).first().tags


class TestTaskDelete:

    def test_delete_task(self, test_db, sample_tasks):
        tid = sample_tasks[0].id
        test_db.delete(sample_tasks[0])
        test_db.commit()
        assert test_db.query(Task).filter_by(id=tid).first() is None

    def test_delete_task_preserves_profiles(self, test_db, sample_tasks, sample_profiles):
        t = sample_tasks[0]
        profile_ids = [p.id for p in t.profiles]
        test_db.delete(t)
        test_db.commit()
        for pid in profile_ids:
            assert test_db.query(Profile).filter_by(id=pid).first() is not None


class TestTaskIsOverdue:

    def test_overdue_pending_task(self, test_db):
        t = Task(title="Overdue", status="pending", due_date=datetime.now() - timedelta(days=1))
        test_db.add(t)
        test_db.commit()
        assert t.is_overdue() is True

    def test_not_overdue_future_task(self, test_db):
        t = Task(title="Future", status="pending", due_date=datetime.now() + timedelta(days=7))
        test_db.add(t)
        test_db.commit()
        assert t.is_overdue() is False

    def test_completed_task_not_overdue(self, test_db):
        t = Task(title="Done", status="completed", due_date=datetime.now() - timedelta(days=5))
        test_db.add(t)
        test_db.commit()
        assert t.is_overdue() is False

    def test_cancelled_task_not_overdue(self, test_db):
        t = Task(title="Cancelled", status="cancelled", due_date=datetime.now() - timedelta(days=3))
        test_db.add(t)
        test_db.commit()
        assert t.is_overdue() is False

    def test_task_no_due_date_not_overdue(self, test_db):
        t = Task(title="No due", status="pending")
        test_db.add(t)
        test_db.commit()
        assert t.is_overdue() is False


# ============================================================================
# GOAL TESTS
# ============================================================================

class TestGoalCreate:

    def test_create_minimal_goal(self, test_db):
        goal = Goal(title="Grow network")
        test_db.add(goal)
        test_db.commit()

        assert goal.id is not None
        assert goal.title == "Grow network"
        assert goal.status == "active"
        assert goal.priority == "medium"
        assert goal.progress == 0.0
        assert goal.description is None
        assert goal.target_date is None
        assert goal.completed_at is None

    def test_create_full_goal_all_fields(self, test_db):
        target = datetime.now() + timedelta(days=90)
        goal = Goal(
            title="Expand Tech Partnerships",
            description="Build 5 new partnerships in tech sector",
            status="active",
            priority="high",
            progress=25.0,
            target_date=target
        )
        test_db.add(goal)
        test_db.commit()

        assert goal.title == "Expand Tech Partnerships"
        assert goal.description == "Build 5 new partnerships in tech sector"
        assert goal.status == "active"
        assert goal.priority == "high"
        assert goal.progress == 25.0
        assert goal.target_date is not None

    def test_create_goal_all_statuses(self, test_db):
        for status in ["active", "completed", "on_hold", "cancelled"]:
            g = Goal(title=f"Goal {status}", status=status)
            test_db.add(g)
        test_db.commit()
        for status in ["active", "completed", "on_hold", "cancelled"]:
            assert test_db.query(Goal).filter_by(status=status).first() is not None

    def test_create_goal_all_priorities(self, test_db):
        for priority in ["low", "medium", "high", "urgent"]:
            g = Goal(title=f"Goal {priority}", priority=priority)
            test_db.add(g)
        test_db.commit()
        for priority in ["low", "medium", "high", "urgent"]:
            assert test_db.query(Goal).filter_by(priority=priority).first() is not None

    def test_create_goal_with_task_link(self, test_db, sample_tasks):
        goal = Goal(title="Task-linked goal")
        goal.tasks.append(sample_tasks[0])
        goal.tasks.append(sample_tasks[1])
        test_db.add(goal)
        test_db.commit()
        assert len(goal.tasks) == 2

    def test_create_goal_with_profile_link(self, test_db, sample_profiles):
        goal = Goal(title="Profile-linked goal")
        goal.profiles.append(sample_profiles[0])
        test_db.add(goal)
        test_db.commit()
        assert len(goal.profiles) == 1

    def test_create_goal_with_company_link(self, test_db, sample_companies):
        goal = Goal(title="Company-linked goal")
        goal.companies.append(sample_companies[0])
        test_db.add(goal)
        test_db.commit()
        assert len(goal.companies) == 1

    def test_create_goal_with_tag_link(self, test_db, sample_tags):
        goal = Goal(title="Tagged goal")
        goal.tags.append(sample_tags[0])
        test_db.add(goal)
        test_db.commit()
        assert len(goal.tags) == 1

    def test_goal_progress_boundaries(self, test_db):
        g_zero = Goal(title="Zero progress", progress=0.0)
        g_full = Goal(title="Full progress", progress=100.0)
        g_decimal = Goal(title="Decimal progress", progress=33.33)
        test_db.add_all([g_zero, g_full, g_decimal])
        test_db.commit()
        assert g_zero.progress == 0.0
        assert g_full.progress == 100.0
        assert abs(g_decimal.progress - 33.33) < 0.01


class TestGoalRead:

    def test_read_by_id(self, test_db, sample_goals):
        g = test_db.query(Goal).filter_by(id=sample_goals[0].id).first()
        assert g.title == "Expand Tech Partnerships"

    def test_read_all_goals(self, test_db, sample_goals):
        assert test_db.query(Goal).count() == len(sample_goals)

    def test_read_active_goals(self, test_db, sample_goals):
        active = test_db.query(Goal).filter_by(status="active").all()
        assert len(active) == 3

    def test_read_completed_goals(self, test_db, sample_goals):
        completed = test_db.query(Goal).filter_by(status="completed").all()
        assert len(completed) == 1

    def test_read_goals_by_priority_high(self, test_db, sample_goals):
        high = test_db.query(Goal).filter_by(priority="high").all()
        assert len(high) == 2

    def test_read_goal_with_tasks(self, test_db, sample_goals):
        g = test_db.query(Goal).filter_by(title="Expand Tech Partnerships").first()
        assert len(g.tasks) == 1

    def test_read_goal_with_profiles(self, test_db, sample_goals):
        g = test_db.query(Goal).filter_by(title="Expand Tech Partnerships").first()
        assert len(g.profiles) == 1

    def test_read_goal_with_companies(self, test_db, sample_goals):
        g = test_db.query(Goal).filter_by(title="Expand Tech Partnerships").first()
        assert len(g.companies) == 1

    def test_read_goal_with_tags(self, test_db, sample_goals):
        g = test_db.query(Goal).filter_by(title="Expand Tech Partnerships").first()
        assert len(g.tags) == 1

    def test_read_overdue_goals(self, test_db, sample_goals):
        now = datetime.now()
        overdue = test_db.query(Goal).filter(
            Goal.target_date < now,
            Goal.status.notin_(["completed", "cancelled"])
        ).all()
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue Goal"


class TestGoalUpdate:

    def test_update_title(self, test_db, sample_goals):
        g = sample_goals[0]
        g.title = "Updated goal title"
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=g.id).first().title == "Updated goal title"

    def test_update_description(self, test_db, sample_goals):
        g = sample_goals[0]
        g.description = "Revised description"
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=g.id).first().description == "Revised description"

    def test_update_progress_manually(self, test_db, sample_goals):
        g = sample_goals[0]
        g.progress = 65.0
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=g.id).first().progress == 65.0

    def test_complete_goal(self, test_db, sample_goals):
        g = sample_goals[0]
        g.complete()
        test_db.commit()
        refreshed = test_db.query(Goal).filter_by(id=g.id).first()
        assert refreshed.status == "completed"
        assert refreshed.progress == 100.0
        assert refreshed.completed_at is not None

    def test_update_priority(self, test_db, sample_goals):
        g = sample_goals[1]
        g.priority = "urgent"
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=g.id).first().priority == "urgent"

    def test_update_target_date(self, test_db, sample_goals):
        g = sample_goals[0]
        new_date = datetime.now() + timedelta(days=180)
        g.target_date = new_date
        test_db.commit()
        refreshed = test_db.query(Goal).filter_by(id=g.id).first()
        assert abs((refreshed.target_date - new_date).total_seconds()) < 2

    def test_clear_target_date(self, test_db, sample_goals):
        g = sample_goals[0]
        g.target_date = None
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=g.id).first().target_date is None

    def test_add_task_to_goal(self, test_db, sample_goals, sample_tasks):
        g = sample_goals[1]
        initial = len(g.tasks)
        g.tasks.append(sample_tasks[3])
        test_db.commit()
        assert len(test_db.query(Goal).filter_by(id=g.id).first().tasks) == initial + 1

    def test_add_profile_to_goal(self, test_db, sample_goals, sample_profiles):
        g = sample_goals[0]
        initial = len(g.profiles)
        g.profiles.append(sample_profiles[1])
        test_db.commit()
        assert len(test_db.query(Goal).filter_by(id=g.id).first().profiles) == initial + 1

    def test_unlink_task_from_goal(self, test_db, sample_goals, sample_tasks):
        g = sample_goals[0]
        task = g.tasks[0]
        g.tasks.remove(task)
        test_db.commit()
        assert len(test_db.query(Goal).filter_by(id=g.id).first().tasks) == 0

    def test_unlink_profile_from_goal(self, test_db, sample_goals, sample_profiles):
        g = sample_goals[0]
        profile = g.profiles[0]
        g.profiles.remove(profile)
        test_db.commit()
        assert len(test_db.query(Goal).filter_by(id=g.id).first().profiles) == 0


class TestGoalProgressCalculation:

    def test_calculate_progress_no_tasks(self, test_db):
        g = Goal(title="No tasks")
        test_db.add(g)
        test_db.commit()
        assert g.calculate_progress() == 0.0

    def test_calculate_progress_all_pending(self, test_db, sample_tasks):
        g = Goal(title="All pending")
        g.tasks.append(sample_tasks[0])
        g.tasks.append(sample_tasks[3])
        test_db.add(g)
        test_db.commit()
        assert g.calculate_progress() == 0.0

    def test_calculate_progress_half_completed(self, test_db, sample_tasks):
        g = Goal(title="Half done")
        g.tasks.append(sample_tasks[0])   # pending
        g.tasks.append(sample_tasks[2])   # completed
        test_db.add(g)
        test_db.commit()
        assert g.calculate_progress() == 50.0

    def test_calculate_progress_all_completed(self, test_db):
        t1 = Task(title="Done A", status="completed")
        t2 = Task(title="Done B", status="completed")
        test_db.add_all([t1, t2])
        test_db.commit()
        g = Goal(title="All done")
        g.tasks.append(t1)
        g.tasks.append(t2)
        test_db.add(g)
        test_db.commit()
        assert g.calculate_progress() == 100.0

    def test_update_progress_syncs(self, test_db, sample_tasks):
        g = Goal(title="Auto progress")
        g.tasks.append(sample_tasks[0])
        g.tasks.append(sample_tasks[2])
        test_db.add(g)
        test_db.commit()
        g.update_progress()
        test_db.commit()
        assert g.progress == 50.0

    def test_auto_complete_at_100_percent(self, test_db):
        t1 = Task(title="T1", status="completed")
        t2 = Task(title="T2", status="completed")
        test_db.add_all([t1, t2])
        test_db.commit()
        g = Goal(title="Auto complete")
        g.tasks.append(t1)
        g.tasks.append(t2)
        test_db.add(g)
        test_db.commit()
        g.update_progress()
        test_db.commit()
        assert g.status == "completed"
        assert g.completed_at is not None


class TestGoalDelete:

    def test_delete_goal(self, test_db, sample_goals):
        gid = sample_goals[0].id
        test_db.delete(sample_goals[0])
        test_db.commit()
        assert test_db.query(Goal).filter_by(id=gid).first() is None

    def test_delete_goal_preserves_tasks(self, test_db, sample_goals, sample_tasks):
        g = sample_goals[0]
        task_ids = [t.id for t in g.tasks]
        test_db.delete(g)
        test_db.commit()
        for tid in task_ids:
            assert test_db.query(Task).filter_by(id=tid).first() is not None

    def test_delete_goal_preserves_profiles(self, test_db, sample_goals, sample_profiles):
        g = sample_goals[0]
        profile_ids = [p.id for p in g.profiles]
        test_db.delete(g)
        test_db.commit()
        for pid in profile_ids:
            assert test_db.query(Profile).filter_by(id=pid).first() is not None


class TestGoalIsOverdue:

    def test_overdue_active_goal(self, test_db):
        g = Goal(title="Overdue", status="active", target_date=datetime.now() - timedelta(days=1))
        test_db.add(g)
        test_db.commit()
        assert g.is_overdue() is True

    def test_not_overdue_future_goal(self, test_db):
        g = Goal(title="Future", status="active", target_date=datetime.now() + timedelta(days=30))
        test_db.add(g)
        test_db.commit()
        assert g.is_overdue() is False

    def test_completed_goal_not_overdue(self, test_db):
        g = Goal(title="Done", status="completed", target_date=datetime.now() - timedelta(days=10))
        test_db.add(g)
        test_db.commit()
        assert g.is_overdue() is False

    def test_goal_no_target_date_not_overdue(self, test_db):
        g = Goal(title="No target", status="active")
        test_db.add(g)
        test_db.commit()
        assert g.is_overdue() is False


class TestGoalGetSummary:

    def test_get_summary_has_all_keys(self, test_db, sample_goals):
        summary = sample_goals[0].get_summary()
        assert 'total_tasks' in summary
        assert 'completed_tasks' in summary
        assert 'in_progress_tasks' in summary
        assert 'pending_tasks' in summary
        assert 'total_profiles' in summary
        assert 'total_companies' in summary
        assert 'progress' in summary
        assert 'is_overdue' in summary

    def test_get_summary_counts_correct(self, test_db, sample_goals):
        summary = sample_goals[0].get_summary()
        assert summary['total_tasks'] == 1
        assert summary['total_profiles'] == 1
        assert summary['total_companies'] == 1


class TestTaskGoalIntegration:

    def test_completing_task_updates_goal_progress(self, test_db):
        t1 = Task(title="Task A", status="pending")
        t2 = Task(title="Task B", status="pending")
        test_db.add_all([t1, t2])
        test_db.commit()
        g = Goal(title="Integration goal")
        g.tasks.append(t1)
        g.tasks.append(t2)
        test_db.add(g)
        test_db.commit()
        assert g.progress == 0.0
        t1.complete()
        test_db.commit()
        g.update_progress()
        test_db.commit()
        assert g.progress == 50.0

    def test_all_tasks_complete_auto_completes_goal(self, test_db):
        t1 = Task(title="Final A", status="pending")
        t2 = Task(title="Final B", status="pending")
        test_db.add_all([t1, t2])
        test_db.commit()
        g = Goal(title="Auto-complete goal")
        g.tasks.append(t1)
        g.tasks.append(t2)
        test_db.add(g)
        test_db.commit()
        t1.complete()
        t2.complete()
        g.update_progress()
        test_db.commit()
        assert g.status == "completed"
        assert g.progress == 100.0
        assert g.completed_at is not None

    def test_manual_100_percent_no_auto_complete(self, test_db):
        """Manual progress=100 without update_progress doesn't change status"""
        g = Goal(title="Manual 100", progress=100.0, status="active")
        test_db.add(g)
        test_db.commit()
        assert g.status == "active"
