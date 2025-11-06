"""
Background task management for AI operations

Allows AI queries to run in background threads while user navigates menus.
"""

import threading
import time
import queue
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Task status enum"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Represents a background AI task"""
    task_id: str
    description: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: str = ""


class BackgroundTaskManager:
    """Singleton manager for background tasks"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_counter = 0
        self.result_queue = queue.Queue()
        self._lock = threading.Lock()

    def create_task(self, description: str, func: Callable, *args, **kwargs) -> str:
        """Create and start a background task

        Args:
            description: Human-readable task description
            func: Function to run in background
            *args, **kwargs: Arguments to pass to function

        Returns:
            task_id: Unique identifier for the task
        """
        with self._lock:
            self.task_counter += 1
            task_id = f"task_{self.task_counter}"

            task = BackgroundTask(
                task_id=task_id,
                description=description,
                status=TaskStatus.QUEUED,
                started_at=datetime.now()
            )

            self.tasks[task_id] = task

        # Start thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, func, args, kwargs),
            daemon=True
        )
        thread.start()

        return task_id

    def _run_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict):
        """Run a task in background thread"""
        try:
            # Update status to running
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.RUNNING

            # Execute function
            result = func(*args, **kwargs)

            # Update with result
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.COMPLETED
                    self.tasks[task_id].completed_at = datetime.now()
                    self.tasks[task_id].result = result

            # Notify completion
            self.result_queue.put(task_id)

        except Exception as e:
            # Handle error
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.FAILED
                    self.tasks[task_id].completed_at = datetime.now()
                    self.tasks[task_id].error = str(e)

            self.result_queue.put(task_id)

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID"""
        with self._lock:
            return self.tasks.get(task_id)

    def get_running_tasks(self) -> List[BackgroundTask]:
        """Get all running tasks"""
        with self._lock:
            return [
                task for task in self.tasks.values()
                if task.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]
            ]

    def get_completed_tasks(self) -> List[BackgroundTask]:
        """Get all completed tasks"""
        with self._lock:
            return [
                task for task in self.tasks.values()
                if task.status == TaskStatus.COMPLETED
            ]

    def get_pending_results(self) -> List[str]:
        """Get task IDs with pending results"""
        results = []
        while not self.result_queue.empty():
            try:
                results.append(self.result_queue.get_nowait())
            except queue.Empty:
                break
        return results

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task (marks as cancelled, thread may still complete)"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]:
                    task.status = TaskStatus.CANCELLED
                    return True
        return False

    def clear_completed(self):
        """Clear completed tasks"""
        with self._lock:
            self.tasks = {
                tid: task for tid, task in self.tasks.items()
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            }

    def get_status_summary(self) -> str:
        """Get a summary of task status"""
        running = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        queued = len([t for t in self.tasks.values() if t.status == TaskStatus.QUEUED])
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])

        if running + queued == 0:
            return ""

        parts = []
        if running > 0:
            parts.append(f"🔄 {running} running")
        if queued > 0:
            parts.append(f"⏳ {queued} queued")
        if completed > 0:
            parts.append(f"✅ {completed} ready")

        return " • ".join(parts)


# Global instance
task_manager = BackgroundTaskManager()
