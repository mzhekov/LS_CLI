#!/usr/bin/env python3
"""
Debug script to check Claude Assistant task status
"""

from leadsauce.utils.claude_assistant import get_claude_assistant
from pathlib import Path
from rich.console import Console
import time
import subprocess

console = Console()

def main():
    assistant = get_claude_assistant()

    console.print("\n[bold cyan]Claude Assistant Debug Info[/bold cyan]\n")

    # Check tmux session
    console.print("[yellow]1. Tmux Session Status:[/yellow]")
    if assistant.session_exists():
        console.print("   ✓ Session exists")

        # Check what's running in tmux
        result = subprocess.run([
            "tmux", "display-message", "-t", assistant.SESSION_NAME, "-p", "#{pane_current_command}"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            console.print(f"   Running: [cyan]{result.stdout.strip()}[/cyan]")
    else:
        console.print("   ✗ Session not running")

    # Check results directory
    console.print(f"\n[yellow]2. Results Directory:[/yellow]")
    console.print(f"   Path: {assistant.RESULTS_DIR}")
    console.print(f"   Exists: {assistant.RESULTS_DIR.exists()}")

    if assistant.RESULTS_DIR.exists():
        all_files = list(assistant.RESULTS_DIR.glob("task_*"))
        console.print(f"   Files: {len(all_files)}")

    # Check tasks
    console.print(f"\n[yellow]3. Tasks:[/yellow]")
    tasks = assistant.get_tasks()
    console.print(f"   Total: {len(tasks)}")

    running = [t for t in tasks if t.status == "running"]
    if running:
        console.print(f"\n   [cyan]Running Tasks ({len(running)}):[/cyan]")
        for task in running:
            elapsed = int(time.time() - task.timestamp)
            console.print(f"\n   Task #{task.ticket_id}")
            console.print(f"   Command: {task.command[:50]}")
            console.print(f"   Running for: {elapsed} seconds ({elapsed//60} minutes)")
            console.print(f"   Result file: {task.result_file}")

            if task.result_file:
                result_path = Path(task.result_file)
                console.print(f"   Result exists: {result_path.exists()}")

                if result_path.exists():
                    size = result_path.stat().st_size
                    console.print(f"   File size: {size} bytes")

                    if size > 0:
                        with open(result_path, 'r') as f:
                            content = f.read()

                        console.print(f"\n   [dim]--- First 300 chars ---[/dim]")
                        console.print(f"   {content[:300]}")

                        if f"TASK_COMPLETE_{task.ticket_id}" in content:
                            console.print("\n   [green]✓ Completion marker found![/green]")
                        else:
                            console.print("\n   [yellow]⚠ No completion marker yet[/yellow]")

                # Check for script files
                prompt_file = assistant.RESULTS_DIR / f"task_{task.ticket_id}_prompt.txt"
                script_file = assistant.RESULTS_DIR / f"task_{task.ticket_id}_script.sh"

                console.print(f"\n   Prompt file exists: {prompt_file.exists()}")
                console.print(f"   Script file exists: {script_file.exists()}")

                if script_file.exists():
                    console.print(f"\n   [dim]--- Script content ---[/dim]")
                    with open(script_file, 'r') as f:
                        console.print(f"   {f.read()}")

    console.print()

if __name__ == "__main__":
    main()
