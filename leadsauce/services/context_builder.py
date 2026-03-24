"""
ContextBuilder — queries the LeadSauce DB and produces a [CONTEXT] block
that the AI assistant uses to stay grounded in Miro's current reality.
"""

from datetime import datetime, timedelta
from typing import Optional
from leadsauce.utils.db import DatabaseSession
from leadsauce.models.task import Task
from leadsauce.models.goal import Goal
from leadsauce.models.reminder import Reminder
from leadsauce.models.conversation import Conversation


class ContextBuilder:
    """Builds structured context snapshots from live DB data."""

    # How many days ahead to show reminders
    REMINDER_HORIZON_DAYS = 7
    # How many recent interactions to surface
    MAX_REMINDERS = 5
    MAX_GOALS = 6
    # History window for "last seen" calc
    HISTORY_DAYS = 30

    def build_context_block(self, external_context: Optional[str] = None) -> str:
        """
        Returns a formatted [CONTEXT]...[/CONTEXT] block ready for injection
        into the AI prompt.

        Args:
            external_context: Additional context from n8n (calendar events, etc.)
        """
        data = self.get_raw_context()
        lines = ["[CONTEXT]"]

        # --- Last check-in ---
        if data['days_since_checkin'] is None:
            lines.append("Last check-in: never")
        elif data['days_since_checkin'] == 0:
            lines.append("Last check-in: today")
        elif data['days_since_checkin'] == 1:
            lines.append("Last check-in: yesterday")
        else:
            lines.append(f"Last check-in: {data['days_since_checkin']} days ago")

        # --- Last commitment ---
        if data['last_commitment']:
            lines.append(f"Last commitment: \"{data['last_commitment']}\"")

        # --- Tasks ---
        total = data['task_counts']['total']
        overdue = data['task_counts']['overdue']
        in_progress = data['task_counts']['in_progress']
        if total > 0:
            task_line = f"Open tasks: {total}"
            details = []
            if overdue:
                details.append(f"{overdue} overdue")
            if in_progress:
                details.append(f"{in_progress} in progress")
            if details:
                task_line += f" ({', '.join(details)})"
            lines.append(task_line)
        else:
            lines.append("Open tasks: none")

        # --- Goals ---
        if data['goals']:
            goal_parts = []
            for g in data['goals']:
                pct = int(g['progress'])
                goal_parts.append(f"{g['title']} ({pct}%)")
            lines.append(f"Active goals: {', '.join(goal_parts)}")

        # --- Reminders ---
        if data['upcoming_reminders']:
            reminder_parts = []
            for r in data['upcoming_reminders']:
                due = r['due_label']
                reminder_parts.append(f"\"{r['title']}\" {due}")
            lines.append(f"Upcoming: {'; '.join(reminder_parts)}")

        # --- External context (calendar, etc. from n8n) ---
        if external_context and external_context.strip():
            lines.append(f"Calendar/external: {external_context.strip()}")

        lines.append("[/CONTEXT]")
        return "\n".join(lines)

    def get_raw_context(self) -> dict:
        """Returns raw context data as a dictionary (useful for API responses)."""
        with DatabaseSession() as session:
            now = datetime.utcnow()

            # Task counts
            task_counts = self._get_task_counts(session, now)

            # Active goals with progress
            goals = self._get_active_goals(session)

            # Upcoming reminders
            upcoming_reminders = self._get_upcoming_reminders(session, now)

            # Last check-in / commitment
            days_since_checkin, last_commitment = self._get_checkin_info(session, now)

            return {
                'task_counts': task_counts,
                'goals': goals,
                'upcoming_reminders': upcoming_reminders,
                'days_since_checkin': days_since_checkin,
                'last_commitment': last_commitment,
                'generated_at': now.isoformat(),
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_task_counts(self, session, now: datetime) -> dict:
        active_tasks = (
            session.query(Task)
            .filter(Task.status.in_(['pending', 'in_progress']))
            .all()
        )
        overdue = sum(1 for t in active_tasks if t.is_overdue())
        in_progress = sum(1 for t in active_tasks if t.status == 'in_progress')
        return {
            'total': len(active_tasks),
            'overdue': overdue,
            'in_progress': in_progress,
        }

    def _get_active_goals(self, session) -> list:
        goals = (
            session.query(Goal)
            .filter(Goal.status == 'active')
            .order_by(Goal.priority.desc(), Goal.progress.desc())
            .limit(self.MAX_GOALS)
            .all()
        )
        return [
            {'title': g.title, 'progress': g.progress or 0.0, 'priority': g.priority}
            for g in goals
        ]

    def _get_upcoming_reminders(self, session, now: datetime) -> list:
        horizon = now + timedelta(days=self.REMINDER_HORIZON_DAYS)
        reminders = (
            session.query(Reminder)
            .filter(
                Reminder.completed == False,
                Reminder.reminder_date != None,
                Reminder.reminder_date >= now,
                Reminder.reminder_date <= horizon,
            )
            .order_by(Reminder.reminder_date.asc())
            .limit(self.MAX_REMINDERS)
            .all()
        )

        result = []
        for r in reminders:
            delta = r.reminder_date - now
            if delta.days == 0:
                due_label = "due today"
            elif delta.days == 1:
                due_label = "due tomorrow"
            else:
                due_label = f"in {delta.days} days"
            result.append({'title': r.title, 'due_label': due_label, 'due_date': r.reminder_date.isoformat()})

        return result

    def _get_checkin_info(self, session, now: datetime):
        """Returns (days_since_last_checkin, last_user_message_content)."""
        last_msg = (
            session.query(Conversation)
            .filter(Conversation.role == 'user')
            .order_by(Conversation.created_at.desc())
            .first()
        )

        if last_msg is None:
            return None, None

        delta = now - last_msg.created_at
        days = delta.days

        # Use the last user message as the "last commitment" (truncated)
        commitment = last_msg.content.strip()
        if len(commitment) > 120:
            commitment = commitment[:117] + "..."

        return days, commitment
