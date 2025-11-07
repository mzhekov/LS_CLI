#!/usr/bin/env python3
"""
Quick script to manage stuck Claude Assistant tasks
"""

from leadsauce.utils.claude_assistant import get_claude_assistant
from rich.console import Console

console = Console()

def main():
    assistant = get_claude_assistant()

    console.print("\n[bold cyan]Claude Assistant Task Manager[/bold cyan]\n")

    # Show current tasks
    tasks = assistant.get_tasks()
    if not tasks:
        console.print("[yellow]No tasks found[/yellow]\n")
        return

    console.print(f"Total tasks: {len(tasks)}")
    running_tasks = [t for t in tasks if t.status == "running"]
    console.print(f"Running tasks: {len(running_tasks)}")

    # Check for stuck tasks
    import time
    stuck_tasks = [t for t in running_tasks if (time.time() - t.timestamp) > 3600]

    if stuck_tasks:
        console.print(f"\n[yellow]⚠ Found {len(stuck_tasks)} stuck task(s) (running > 1 hour)[/yellow]\n")

        for task in stuck_tasks:
            time_ago = (time.time() - task.timestamp) / 3600
            console.print(f"  • Ticket #{task.ticket_id}: {task.command[:50]}")
            console.print(f"    Started: {time_ago:.1f} hours ago\n")

        response = input("Clear these stuck tasks? (y/n): ")
        if response.lower() == 'y':
            updated = assistant.clear_stuck_tasks()
            if updated:
                console.print("[green]✓ Cleared stuck tasks[/green]\n")
            else:
                console.print("[yellow]No tasks were cleared[/yellow]\n")
    else:
        console.print("\n[green]✓ No stuck tasks found[/green]\n")

    # Option to clear all tasks
    if len(tasks) > 0:
        response = input("Clear ALL tasks? (y/n): ")
        if response.lower() == 'y':
            assistant._save_all_tasks([])
            console.print("[green]✓ Cleared all tasks[/green]\n")

if __name__ == "__main__":
    main()
