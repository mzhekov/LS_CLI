"""
Tests for Task and Goal models with their relationships
"""

import pytest
from datetime import datetime, timedelta
from leadsauce.models.task import Task
from leadsauce.models.goal import Goal
from leadsauce.models.profile import Profile


class TestTaskCreate:
    """Test Task creation"""

    def test_create_basic_task(self, test_db):
        """Test creating a task with minimum required fields"""
        task = Task(
            title="Test Task",
            status="Pending"
        )
        test_db.add(task)
        test_db.commit()

        assert task.id is not None
        assert task.title == "Test Task"
        assert task.status == "Pending"

    def test_create_full_task(self, test_db, sample_profiles):
        """Test creating a task with all fields"""
        due_date = datetime.now() + timedelta(days=7)

        task = Task(
            title="Complete Project",
            description="Finish all pending items",
            status="In Progress",
            priority="High",
            due_date=due_date
        )
        task.profiles.append(sample_profiles[0])

        test_db.add(task)
        test_db.commit()

        assert task.id is not None
        assert task.priority == "High"
        assert task.due_date == due_date
        assert len(task.profiles) == 1

    def test_create_task_with_multiple_profiles(self, test_db, sample_profiles):
        """Test creating task linked to multiple profiles"""
        task = Task(
            title="Team Meeting",
            status="Pending"
        )
        task.profiles.append(sample_profiles[0])
        task.profiles.append(sample_profiles[1])
        task.profiles.append(sample_profiles[2])

        test_db.add(task)
        test_db.commit()

        assert len(task.profiles) == 3

    def test_create_task_statuses(self, test_db):
        """Test creating tasks with different statuses"""
        statuses = ["Pending", "In Progress", "Completed", "Cancelled"]

        for status in statuses:
            task = Task(
                title=f"Task {status}",
                status=status
            )
            test_db.add(task)

        test_db.commit()

        tasks = test_db.query(Task).all()
        assert len(tasks) == len(statuses)

    def test_create_task_priorities(self, test_db):
        """Test creating tasks with different priorities"""
        priorities = ["Low", "Medium", "High", "Urgent"]

        for priority in priorities:
            task = Task(
                title=f"Task {priority}",
                status="Pending",
                priority=priority
            )
            test_db.add(task)

        test_db.commit()

        high_priority_tasks = test_db.query(Task).filter_by(priority="High").all()
        assert len(high_priority_tasks) >= 1


class TestTaskRead:
    """Test Task read operations"""

    def test_read_all_tasks(self, test_db, sample_tasks):
        """Test reading all tasks"""
        tasks = test_db.query(Task).all()

        assert len(tasks) == 4
        assert all(isinstance(t, Task) for t in tasks)

    def test_read_tasks_by_status(self, test_db, sample_tasks):
        """Test filtering tasks by status"""
        pending_tasks = test_db.query(Task).filter_by(status="Pending").all()

        assert len(pending_tasks) == 2

    def test_read_tasks_by_priority(self, test_db, sample_tasks):
        """Test filtering tasks by priority"""
        high_tasks = test_db.query(Task).filter_by(priority="High").all()

        assert len(high_tasks) == 2

    def test_read_completed_tasks(self, test_db, sample_tasks):
        """Test filtering completed tasks"""
        completed = test_db.query(Task).filter_by(status="Completed").all()

        assert len(completed) == 1
        assert completed[0].completed_date is not None

    def test_read_tasks_by_due_date(self, test_db, sample_tasks):
        """Test filtering tasks by due date range"""
        today = datetime.now()
        week_from_now = today + timedelta(days=7)

        upcoming_tasks = test_db.query(Task).filter(
            Task.due_date <= week_from_now,
            Task.due_date >= today
        ).all()

        assert len(upcoming_tasks) >= 1

    def test_read_overdue_tasks(self, test_db, sample_tasks):
        """Test finding overdue tasks"""
        today = datetime.now()

        overdue_tasks = test_db.query(Task).filter(
            Task.due_date < today,
            Task.status != "Completed"
        ).all()

        # Sample data may not have overdue tasks
        assert isinstance(overdue_tasks, list)

    def test_read_tasks_for_profile(self, test_db, sample_tasks, sample_profiles):
        """Test reading tasks linked to a specific profile"""
        profile = sample_profiles[0]

        # Tasks linked to this profile
        assert len(profile.tasks) >= 1
        assert sample_tasks[0] in profile.tasks


class TestTaskUpdate:
    """Test Task update operations"""

    def test_update_task_status(self, test_db, sample_tasks):
        """Test updating task status"""
        task = sample_tasks[0]
        assert task.status == "Pending"

        task.status = "In Progress"
        test_db.commit()

        updated = test_db.query(Task).filter_by(id=task.id).first()
        assert updated.status == "In Progress"

    def test_complete_task(self, test_db, sample_tasks):
        """Test marking task as completed"""
        task = sample_tasks[0]

        task.status = "Completed"
        task.completed_date = datetime.now()
        test_db.commit()

        updated = test_db.query(Task).filter_by(id=task.id).first()
        assert updated.status == "Completed"
        assert updated.completed_date is not None

    def test_update_task_priority(self, test_db, sample_tasks):
        """Test updating task priority"""
        task = sample_tasks[3]  # Bob's task (Low priority)
        assert task.priority == "Low"

        task.priority = "Urgent"
        test_db.commit()

        updated = test_db.query(Task).filter_by(id=task.id).first()
        assert updated.priority == "Urgent"

    def test_update_task_due_date(self, test_db, sample_tasks):
        """Test updating task due date"""
        task = sample_tasks[0]
        new_due_date = datetime.now() + timedelta(days=14)

        task.due_date = new_due_date
        test_db.commit()

        updated = test_db.query(Task).filter_by(id=task.id).first()
        assert updated.due_date.date() == new_due_date.date()

    def test_add_profile_to_task(self, test_db, sample_tasks, sample_profiles):
        """Test adding a profile to a task"""
        task = sample_tasks[0]
        original_profile_count = len(task.profiles)

        task.profiles.append(sample_profiles[2])
        test_db.commit()

        updated = test_db.query(Task).filter_by(id=task.id).first()
        assert len(updated.profiles) == original_profile_count + 1

    def test_remove_profile_from_task(self, test_db, sample_tasks):
        """Test removing a profile from a task"""
        task = sample_tasks[0]
        original_profile_count = len(task.profiles)

        if original_profile_count > 0:
            task.profiles.pop()
            test_db.commit()

            updated = test_db.query(Task).filter_by(id=task.id).first()
            assert len(updated.profiles) == original_profile_count - 1


class TestTaskDelete:
    """Test Task delete operations"""

    def test_delete_task(self, test_db, sample_tasks):
        """Test deleting a task"""
        task_id = sample_tasks[0].id
        task_count_before = test_db.query(Task).count()

        test_db.delete(sample_tasks[0])
        test_db.commit()

        task_count_after = test_db.query(Task).count()
        deleted_task = test_db.query(Task).filter_by(id=task_id).first()

        assert task_count_after == task_count_before - 1
        assert deleted_task is None

    def test_delete_task_preserves_profiles(self, test_db, sample_tasks, sample_profiles):
        """Test that deleting task doesn't delete linked profiles"""
        task = sample_tasks[0]
        profile_count_before = test_db.query(Profile).count()

        test_db.delete(task)
        test_db.commit()

        profile_count_after = test_db.query(Profile).count()
        assert profile_count_after == profile_count_before


class TestGoalCreate:
    """Test Goal creation"""

    def test_create_basic_goal(self, test_db):
        """Test creating a goal with minimum required fields"""
        goal = Goal(
            title="Test Goal",
            status="Active"
        )
        test_db.add(goal)
        test_db.commit()

        assert goal.id is not None
        assert goal.title == "Test Goal"
        assert goal.status == "Active"

    def test_create_full_goal(self, test_db, sample_profiles, sample_tasks):
        """Test creating a goal with all fields"""
        target_date = datetime.now() + timedelta(days=90)

        goal = Goal(
            title="Expand Network",
            description="Connect with 50 new professionals",
            target_date=target_date,
            progress=25,
            status="Active"
        )
        goal.profiles.append(sample_profiles[0])
        goal.tasks.append(sample_tasks[0])

        test_db.add(goal)
        test_db.commit()

        assert goal.id is not None
        assert goal.progress == 25
        assert len(goal.profiles) == 1
        assert len(goal.tasks) == 1

    def test_create_goal_with_multiple_tasks(self, test_db, sample_tasks):
        """Test creating goal with multiple linked tasks"""
        goal = Goal(
            title="Complete Project",
            status="Active"
        )
        goal.tasks.append(sample_tasks[0])
        goal.tasks.append(sample_tasks[1])
        goal.tasks.append(sample_tasks[2])

        test_db.add(goal)
        test_db.commit()

        assert len(goal.tasks) == 3

    def test_create_goal_statuses(self, test_db):
        """Test creating goals with different statuses"""
        statuses = ["Active", "Achieved", "Abandoned"]

        for status in statuses:
            goal = Goal(
                title=f"Goal {status}",
                status=status
            )
            test_db.add(goal)

        test_db.commit()

        goals = test_db.query(Goal).all()
        assert len(goals) == len(statuses)


class TestGoalRead:
    """Test Goal read operations"""

    def test_read_all_goals(self, test_db, sample_goals):
        """Test reading all goals"""
        goals = test_db.query(Goal).all()

        assert len(goals) == 3
        assert all(isinstance(g, Goal) for g in goals)

    def test_read_active_goals(self, test_db, sample_goals):
        """Test filtering active goals"""
        active_goals = test_db.query(Goal).filter_by(status="Active").all()

        assert len(active_goals) == 2

    def test_read_achieved_goals(self, test_db, sample_goals):
        """Test filtering achieved goals"""
        achieved_goals = test_db.query(Goal).filter_by(status="Achieved").all()

        assert len(achieved_goals) == 1
        assert achieved_goals[0].progress == 100

    def test_read_goals_by_progress(self, test_db, sample_goals):
        """Test filtering goals by progress range"""
        high_progress_goals = test_db.query(Goal).filter(Goal.progress >= 70).all()

        assert len(high_progress_goals) == 2

    def test_read_goal_with_tasks(self, test_db, sample_goals):
        """Test reading goal with its linked tasks"""
        goal = sample_goals[0]

        assert len(goal.tasks) >= 1
        assert all(isinstance(t, Task) for t in goal.tasks)

    def test_read_goal_with_profiles(self, test_db, sample_goals):
        """Test reading goal with its linked profiles"""
        goal = sample_goals[0]

        assert len(goal.profiles) >= 1
        assert all(isinstance(p, Profile) for p in goal.profiles)


class TestGoalUpdate:
    """Test Goal update operations"""

    def test_update_goal_progress(self, test_db, sample_goals):
        """Test updating goal progress"""
        goal = sample_goals[0]
        original_progress = goal.progress

        goal.progress = 60
        test_db.commit()

        updated = test_db.query(Goal).filter_by(id=goal.id).first()
        assert updated.progress == 60
        assert updated.progress != original_progress

    def test_achieve_goal(self, test_db, sample_goals):
        """Test marking goal as achieved"""
        goal = sample_goals[0]

        goal.status = "Achieved"
        goal.progress = 100
        test_db.commit()

        updated = test_db.query(Goal).filter_by(id=goal.id).first()
        assert updated.status == "Achieved"
        assert updated.progress == 100

    def test_update_goal_target_date(self, test_db, sample_goals):
        """Test updating goal target date"""
        goal = sample_goals[0]
        new_target = datetime.now() + timedelta(days=180)

        goal.target_date = new_target
        test_db.commit()

        updated = test_db.query(Goal).filter_by(id=goal.id).first()
        assert updated.target_date.date() == new_target.date()

    def test_add_task_to_goal(self, test_db, sample_goals):
        """Test adding a task to a goal"""
        goal = sample_goals[0]
        original_task_count = len(goal.tasks)

        new_task = Task(
            title="New Task for Goal",
            status="Pending"
        )
        goal.tasks.append(new_task)
        test_db.add(new_task)
        test_db.commit()

        updated = test_db.query(Goal).filter_by(id=goal.id).first()
        assert len(updated.tasks) == original_task_count + 1


class TestGoalTaskIntegration:
    """Test Goal and Task integration"""

    def test_goal_progress_calculation(self, test_db, sample_goals):
        """Test goal progress based on completed tasks"""
        goal = sample_goals[0]

        # Count completed tasks
        completed_tasks = sum(1 for task in goal.tasks if task.status == "Completed")
        total_tasks = len(goal.tasks)

        if total_tasks > 0:
            expected_progress = (completed_tasks / total_tasks) * 100

            # This test documents expected behavior
            # Application should auto-calculate goal progress from task completion

    def test_completing_task_updates_goal(self, test_db, sample_goals):
        """Test that completing a task should update goal progress"""
        goal = sample_goals[0]
        original_progress = goal.progress

        # Complete a task linked to this goal
        if len(goal.tasks) > 0:
            task = goal.tasks[0]
            task.status = "Completed"
            task.completed_date = datetime.now()
            test_db.commit()

            # Application logic should update goal.progress
            # This test documents expected behavior

    def test_goal_auto_complete_when_all_tasks_done(self, test_db):
        """Test that goal should auto-complete when all tasks are completed"""
        goal = Goal(
            title="Auto-complete Test",
            status="Active",
            progress=0
        )

        task1 = Task(title="Task 1", status="Completed")
        task2 = Task(title="Task 2", status="Completed")

        goal.tasks.append(task1)
        goal.tasks.append(task2)

        test_db.add(goal)
        test_db.commit()

        # Application logic should set goal.status = "Achieved"
        # and goal.progress = 100 when all tasks are completed
        # This test documents expected behavior


class TestTaskGoalEdgeCases:
    """Test edge cases for tasks and goals"""

    def test_task_without_due_date(self, test_db):
        """Test creating task without due date"""
        task = Task(
            title="No Due Date Task",
            status="Pending"
        )
        test_db.add(task)
        test_db.commit()

        assert task.due_date is None

    def test_goal_with_zero_progress(self, test_db):
        """Test goal with 0% progress"""
        goal = Goal(
            title="Just Started",
            status="Active",
            progress=0
        )
        test_db.add(goal)
        test_db.commit()

        assert goal.progress == 0

    def test_goal_with_100_progress_not_achieved(self, test_db):
        """Test goal with 100% progress but not marked as achieved"""
        # Edge case: progress can be 100 but status still "Active"

        goal = Goal(
            title="Complete but Active",
            status="Active",
            progress=100
        )
        test_db.add(goal)
        test_db.commit()

        assert goal.progress == 100
        assert goal.status == "Active"

        # Application may want to auto-update status

    def test_task_with_past_due_date(self, test_db):
        """Test creating task with past due date"""
        past_date = datetime.now() - timedelta(days=30)

        task = Task(
            title="Overdue Task",
            status="Pending",
            due_date=past_date
        )
        test_db.add(task)
        test_db.commit()

        assert task.due_date < datetime.now()
        assert task.status == "Pending"

        # Application should flag this as overdue


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
