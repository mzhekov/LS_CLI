"""
Background Claude Assistant Service

Allows users to delegate tasks to Claude Code while continuing to work in LeadSauce.
Uses tmux for background sessions and file-based communication.
"""

import os
import subprocess
import tempfile
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

console = Console()


class ClaudeTask:
    """Represents a task sent to Claude"""

    def __init__(self, ticket_id: int, command: str, timestamp: float, status: str = "pending"):
        self.ticket_id = ticket_id
        self.command = command
        self.timestamp = timestamp
        self.status = status  # pending, running, completed, failed
        self.result_file = None

    def to_dict(self) -> dict:
        return {
            'ticket_id': self.ticket_id,
            'command': self.command,
            'timestamp': self.timestamp,
            'status': self.status,
            'result_file': self.result_file
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ClaudeTask':
        task = cls(
            ticket_id=data['ticket_id'],
            command=data['command'],
            timestamp=data['timestamp'],
            status=data['status']
        )
        task.result_file = data.get('result_file')
        return task


class ClaudeAssistantService:
    """Manages background Claude Code session"""

    SESSION_NAME = "leadsauce-claude-assistant"
    QUEUE_FILE = Path(tempfile.gettempdir()) / "leadsauce_claude_queue.json"
    RESULTS_DIR = Path(tempfile.gettempdir()) / "leadsauce_claude_results"

    def __init__(self):
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure necessary directories exist"""
        self.RESULTS_DIR.mkdir(exist_ok=True)

    def is_tmux_available(self) -> bool:
        """Check if tmux is installed"""
        try:
            subprocess.run(["tmux", "-V"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_claude_available(self) -> bool:
        """Check if Claude Code CLI is installed"""
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def session_exists(self) -> bool:
        """Check if Claude assistant tmux session exists"""
        if not self.is_tmux_available():
            return False

        result = subprocess.run(
            ["tmux", "has-session", "-t", self.SESSION_NAME],
            capture_output=True
        )
        return result.returncode == 0

    def start_session(self) -> bool:
        """Start background Claude session in tmux"""
        if not self.is_tmux_available():
            console.print("[red]Error: tmux is not installed[/red]")
            console.print("[yellow]Install tmux: brew install tmux (macOS) or apt install tmux (Linux)[/yellow]")
            return False

        if not self.is_claude_available():
            console.print("[red]Error: Claude Code CLI is not installed[/red]")
            console.print("[yellow]Install from: https://docs.anthropic.com/claude-code[/yellow]")
            return False

        if self.session_exists():
            return True  # Already running

        try:
            # Create detached tmux session with Claude
            subprocess.run([
                "tmux", "new-session", "-d", "-s", self.SESSION_NAME,
                "-x", "120", "-y", "40",  # Set reasonable size
                "claude"
            ], check=True)

            # Give it a moment to start
            time.sleep(1)

            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error starting Claude session: {e}[/red]")
            return False

    def stop_session(self):
        """Stop background Claude session"""
        if self.session_exists():
            subprocess.run(["tmux", "kill-session", "-t", self.SESSION_NAME])

    def send_command(self, command: str, context: Optional[Dict] = None) -> int:
        """Send command to Claude and return ticket ID"""

        # Generate ticket ID
        ticket_id = int(time.time() * 1000)  # Millisecond timestamp

        # Create task
        task = ClaudeTask(
            ticket_id=ticket_id,
            command=command,
            timestamp=time.time(),
            status="pending"
        )

        # Save to queue
        self._save_task(task)

        # Format command for Claude with context
        full_command = command
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"
            full_command = f"{command}{context_str}"

        # Send to tmux session
        try:
            # Send the command
            subprocess.run([
                "tmux", "send-keys", "-t", self.SESSION_NAME,
                full_command, "Enter"
            ], check=True)

            # Update status to running
            task.status = "running"
            self._save_task(task)

            return ticket_id

        except subprocess.CalledProcessError:
            task.status = "failed"
            self._save_task(task)
            return ticket_id

    def get_tasks(self) -> List[ClaudeTask]:
        """Get all tasks from queue"""
        if not self.QUEUE_FILE.exists():
            return []

        try:
            with open(self.QUEUE_FILE, 'r') as f:
                data = json.load(f)
            return [ClaudeTask.from_dict(task_data) for task_data in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def get_task(self, ticket_id: int) -> Optional[ClaudeTask]:
        """Get specific task by ID"""
        tasks = self.get_tasks()
        for task in tasks:
            if task.ticket_id == ticket_id:
                return task
        return None

    def get_pending_count(self) -> int:
        """Get count of pending/running tasks"""
        tasks = self.get_tasks()
        return sum(1 for task in tasks if task.status in ['pending', 'running'])

    def get_completed_unviewed(self) -> List[ClaudeTask]:
        """Get completed tasks that haven't been viewed yet"""
        tasks = self.get_tasks()
        return [task for task in tasks if task.status == 'completed']

    def mark_viewed(self, ticket_id: int):
        """Mark a task as viewed"""
        tasks = self.get_tasks()
        for task in tasks:
            if task.ticket_id == ticket_id:
                task.status = "viewed"
                break
        self._save_all_tasks(tasks)

    def clear_old_tasks(self, hours: int = 24):
        """Clear tasks older than specified hours"""
        tasks = self.get_tasks()
        cutoff = time.time() - (hours * 3600)
        tasks = [task for task in tasks if task.timestamp > cutoff]
        self._save_all_tasks(tasks)

    def _save_task(self, task: ClaudeTask):
        """Save or update a task in the queue"""
        tasks = self.get_tasks()

        # Update if exists, add if new
        found = False
        for i, t in enumerate(tasks):
            if t.ticket_id == task.ticket_id:
                tasks[i] = task
                found = True
                break

        if not found:
            tasks.append(task)

        self._save_all_tasks(tasks)

    def _save_all_tasks(self, tasks: List[ClaudeTask]):
        """Save all tasks to queue file"""
        data = [task.to_dict() for task in tasks]
        with open(self.QUEUE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def show_quick_command_palette(self, context: Optional[Dict] = None) -> Optional[int]:
        """Show quick command palette and send to Claude"""

        console.print()
        console.print(Panel(
            "[bold cyan]💬 Quick Claude Command[/bold cyan]\n\n"
            "[dim]What should Claude do? (agents, code review, analysis, etc.)[/dim]",
            border_style="cyan",
            box=box.ROUNDED
        ))
        console.print()

        command = Prompt.ask("[bold cyan]Claude task[/bold cyan]", console=console)

        if not command or command.strip() == "":
            console.print("[dim]Cancelled[/dim]")
            return None

        # Ensure session is running
        if not self.session_exists():
            console.print("\n[yellow]Starting Claude assistant session...[/yellow]")
            if not self.start_session():
                console.print("[red]Failed to start Claude session[/red]")
                return None
            console.print("[green]✓ Claude session started[/green]\n")

        # Send command
        ticket_id = self.send_command(command, context)

        # Show confirmation
        console.print()
        console.print(f"[green]✓ Sent to Claude[/green] [dim](Ticket #{ticket_id})[/dim]")
        console.print("[dim]Continue working - Press [cyan]Ctrl+R[/cyan] anytime to check results[/dim]")
        console.print()

        time.sleep(1.5)  # Brief pause to see confirmation

        return ticket_id

    def show_results(self):
        """Show Claude results viewer"""

        tasks = self.get_tasks()

        if not tasks:
            console.print()
            console.print(Panel(
                "[yellow]No Claude tasks yet[/yellow]\n\n"
                "Press [cyan]Ctrl+K[/cyan] anywhere to delegate tasks to Claude",
                border_style="yellow",
                title="Claude Results"
            ))
            console.print()
            return

        # Sort by timestamp, newest first
        tasks.sort(key=lambda t: t.timestamp, reverse=True)

        # Build results table
        table = Table(title="Claude Assistant Tasks", show_header=True, header_style="bold cyan")
        table.add_column("Ticket", style="dim", width=12)
        table.add_column("Status", width=10)
        table.add_column("Command", width=50)
        table.add_column("Time", style="dim", width=20)

        for task in tasks[:20]:  # Show last 20 tasks
            # Status with emoji
            if task.status == "completed":
                status = "[green]✓ Done[/green]"
            elif task.status == "running":
                status = "[yellow]⏳ Running[/yellow]"
            elif task.status == "failed":
                status = "[red]✗ Failed[/red]"
            elif task.status == "viewed":
                status = "[dim]✓ Viewed[/dim]"
            else:
                status = "[dim]Pending[/dim]"

            # Truncate command
            cmd = task.command[:47] + "..." if len(task.command) > 50 else task.command

            # Format time
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(task.timestamp))

            table.add_row(
                f"#{task.ticket_id}",
                status,
                cmd,
                time_str
            )

        console.print()
        console.print(table)
        console.print()

        # Show session info
        if self.session_exists():
            console.print("[green]● Claude session running[/green] [dim](tmux session active)[/dim]")
        else:
            console.print("[yellow]○ Claude session not running[/yellow] [dim](will start on first command)[/dim]")

        console.print()
        console.print("[dim]Tips:[/dim]")
        console.print("  • View Claude session: [cyan]tmux attach -t leadsauce-claude-assistant[/cyan]")
        console.print("  • Detach from session: [cyan]Ctrl+B then D[/cyan]")
        console.print("  • Send new task: [cyan]Ctrl+K[/cyan]")
        console.print()


# Global singleton instance
_claude_assistant = None


def get_claude_assistant() -> ClaudeAssistantService:
    """Get global Claude assistant service instance"""
    global _claude_assistant
    if _claude_assistant is None:
        _claude_assistant = ClaudeAssistantService()
    return _claude_assistant


def check_claude_notifications() -> bool:
    """Check if Claude has completed tasks and show notification"""
    assistant = get_claude_assistant()
    completed = assistant.get_completed_unviewed()

    if completed:
        console.print(
            f"[dim]🔔 Claude completed {len(completed)} task(s) - "
            f"Press [cyan]Ctrl+R[/cyan] to view[/dim]"
        )
        return True

    return False
