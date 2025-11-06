"""Interactive AI Assistant for TUI

This module provides an interactive AI assistant interface for the LeadSauce TUI.
Users can ask questions, get coding help, and interact with AI tools directly
from the terminal interface.
"""

import subprocess
import threading
import queue
import time
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
import questionary

from leadsauce.services.ai_cli import AICLIService, ToolNotInstalledError, ToolTimeoutError, AICLIError
from leadsauce.services.system_context import SystemContextProvider
from leadsauce.services.system_executor import SystemExecutor
from leadsauce.utils.background_tasks import task_manager, TaskStatus


class InteractiveAISession:
    """Manage interactive AI assistant sessions in the TUI"""

    def __init__(self, tool: str = 'claude', working_dir: Optional[str] = None, system_aware: bool = True):
        """Initialize interactive AI session

        Args:
            tool: AI tool to use (claude, codex, aider)
            working_dir: Working directory for context
            system_aware: If True, AI can execute LeadSauce system operations
        """
        self.tool = tool
        self.working_dir = working_dir or str(Path.cwd())
        self.console = Console()
        self.service = AICLIService(default_tool=tool)
        self.conversation_history: List[Dict[str, str]] = []
        self.system_aware = system_aware
        self.system_context_sent = False

    def show_welcome(self):
        """Display welcome message"""
        tool_info = self.service.get_tool_info(self.tool)

        system_mode_text = ""
        if self.system_aware:
            system_mode_text = """
**🎯 SYSTEM-AWARE MODE ENABLED:**
The AI can actually perform operations in LeadSauce!
• **Create reminders, profiles, companies, tags**
• **Log interactions and relationships**
• **Search and retrieve data**
• Ask naturally - e.g., "Remind me to call John tomorrow"
"""

        welcome_text = f"""
# 🤖 AI Assistant - {tool_info['name']}

Welcome to the LeadSauce AI Assistant! You can:

• **Ask questions** about your code and data
• **Get help** with LeadSauce features
• **Generate code** snippets and scripts
• **Debug issues** and get suggestions
• **Analyze** your database schema
{system_mode_text}
**Quick Navigation (Single Keypress):**
- Press `1`-`9` or `0` for instant menu switching (no Enter needed!)
  - [1] Dashboard  [2] Profiles  [3] Companies  [4] Network & Relationships
  - [5] Search  [6] Tags  [7] Workshop  [8] Import/Export
  - [9] AI CLI Control  [0] Browser
- Press `?` for help  •  Press `q` to exit

**Usage:**
- Press `Enter` then type your AI query
- Or start typing directly - first character begins your query
- Type `/help` for all commands  •  Type `/menu` for menu dialog
- Type `/context` to add files  •  Type `/clear` to clear history

**Working Directory:** `{self.working_dir}`
        """

        self.console.print(Panel(
            Markdown(welcome_text),
            title="[bold cyan]AI Assistant[/bold cyan]",
            border_style="cyan"
        ))

    def run(self) -> Optional[str]:
        """Run the interactive AI session

        Returns:
            Menu name to navigate to, or None to return to previous menu
        """
        try:
            # Check if tool is installed
            if not self.service.is_installed(self.tool):
                tool_info = self.service.get_tool_info(self.tool)
                self.console.print(Panel(
                    f"[bold red]❌ {tool_info['name']} is not installed[/bold red]\n\n"
                    f"To use this AI assistant, please install:\n"
                    f"[cyan]{tool_info['install_cmd']}[/cyan]",
                    title="Installation Required",
                    border_style="red"
                ))
                self.console.input("\nPress Enter to continue...")
                return None

            context_files = []

            while True:
                try:
                    # Clear screen and show top bar (like web viewer)
                    self.console.clear()
                    from leadsauce.utils.interactive import render_top_bar
                    self.console.print(render_top_bar("AI Assistant"))
                    self.console.print()

                    # Build status panel with current context
                    tool_info = self.service.get_tool_info(self.tool)
                    status_lines = []
                    status_lines.append(f"[bold cyan]🤖 {tool_info['name']}[/]")

                    # Conversation stats
                    msg_count = len(self.conversation_history) // 2  # Pairs of user/assistant
                    status_lines.append(f"[dim]Messages:[/] {msg_count}")

                    # Context files
                    if context_files:
                        status_lines.append(f"[dim]Context files:[/] {len(context_files)}")

                    # Running tasks
                    running_tasks = task_manager.get_running_tasks()
                    if running_tasks:
                        status_lines.append(f"[yellow]⏳ {len(running_tasks)} task(s) running[/]")

                    # Completed tasks waiting for review
                    pending_results = task_manager.get_pending_results()
                    if pending_results:
                        status_lines.append(f"[green]✅ {len(pending_results)} task(s) completed[/] [dim](use /results)[/]")

                    # System-aware mode indicator
                    if self.system_aware:
                        status_lines.append(f"[bold green]🎯 System-Aware Mode[/] [dim](can execute commands)[/]")

                    status_text = " │ ".join(status_lines)
                    self.console.print(Panel(
                        status_text,
                        border_style="cyan",
                        title="[cyan]Session Info[/]"
                    ))
                    self.console.print()

                    # Show condensed shortcuts guide
                    shortcuts = (
                        "[bold cyan]Quick Actions:[/]\n"
                        "[cyan]1-9/0[/] Jump to menu  │  "
                        "[cyan]Ctrl+K[/] Delegate to Claude Code  │  "
                        "[cyan]Ctrl+R[/] View Results  │  "
                        "[cyan]?[/] Help  │  "
                        "[cyan]q[/] Quit  │  "
                        "[cyan]Enter[/] Ask AI"
                    )
                    self.console.print(shortcuts)
                    self.console.print()

                    # Get single key for quick navigation or Enter for full input
                    self.console.print("[dim]Press key for action (or Enter to ask AI):[/]")

                    from leadsauce.utils.interactive import get_single_key
                    key = get_single_key()

                    # Handle single-key menu navigation (1-9, 0)
                    nav_map = {
                        '1': 'Dashboard',
                        '2': 'Profiles',
                        '3': 'Companies',
                        '4': 'Network & Relationships',
                        '5': 'Search',
                        '6': 'Tags',
                        '7': 'Workshop',
                        '8': 'Import/Export',
                        '9': 'AI CLI Control',
                        '0': 'Browser',
                    }

                    if key in nav_map:
                        self.console.print(f"[dim]Switching to {nav_map[key]}...[/]")
                        return nav_map[key]

                    # Handle Ctrl+K - Quick Claude Code Command
                    if key == '\x0b':  # Ctrl+K
                        from leadsauce.utils.claude_assistant import get_claude_assistant
                        assistant = get_claude_assistant()
                        context = {
                            'view': 'AI Assistant',
                            'tool': self.tool,
                            'working_dir': str(self.working_dir),
                            'conversation_messages': len(self.conversation_history)
                        }
                        assistant.show_quick_command_palette(context)
                        continue

                    # Handle Ctrl+R - View Claude Code Results
                    if key == '\x12':  # Ctrl+R
                        from leadsauce.utils.claude_assistant import get_claude_assistant
                        assistant = get_claude_assistant()
                        assistant.show_results()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    # Handle help
                    if key == '?':
                        self._show_help()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    # Handle quit/exit keys
                    if key in ['q', 'Q']:
                        running = task_manager.get_running_tasks()
                        if running:
                            confirm = questionary.confirm(
                                f"{len(running)} task(s) still running. Exit anyway?",
                                default=False
                            ).ask()
                            if not confirm:
                                continue
                        self.console.print("[dim]Exiting AI Assistant...[/dim]")
                        return None

                    # If Enter or any other key, get full text input
                    if key in ['\n', '\r']:
                        # Just Enter pressed - prompt for full input
                        user_input = Prompt.ask(
                            "[bold green]You[/bold green]",
                            console=self.console
                        ).strip()
                    else:
                        # Some other character - include it in the prompt
                        self.console.print(f"[bold green]You[/bold green] {key}", end="")
                        remaining = Prompt.ask("", console=self.console).strip()
                        user_input = (key + remaining).strip()

                    if not user_input:
                        continue

                    # Check for /bg prefix to run in background
                    run_in_bg = False
                    if user_input.lower().startswith('/bg '):
                        run_in_bg = True
                        user_input = user_input[4:].strip()  # Remove /bg prefix

                    # Handle special commands
                    if user_input.lower() in ['/exit', '/quit', '/q']:
                        # Check if tasks are running
                        running = task_manager.get_running_tasks()
                        if running:
                            confirm = questionary.confirm(
                                f"{len(running)} task(s) still running. Exit anyway?",
                                default=False
                            ).ask()
                            if not confirm:
                                continue
                        self.console.print("[dim]Exiting Browser...[/dim]")
                        return None

                    elif user_input.lower() == '/help':
                        self._show_help()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    elif user_input.lower() == '/menu':
                        menu_choice = self._show_menu_navigation()
                        if menu_choice:
                            self.console.print(f"[dim]Switching to {menu_choice}...[/dim]")
                            return menu_choice
                        continue

                    elif user_input.lower() == '/clear':
                        self.conversation_history.clear()
                        context_files.clear()
                        self.console.print("[green]✓[/green] Conversation history cleared")
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    elif user_input.lower() == '/context':
                        context_files = self._add_context_files()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    elif user_input.lower() == '/history':
                        self._show_history()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    elif user_input.lower() == '/status':
                        self._show_status()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    elif user_input.lower() == '/tasks':
                        self._show_background_tasks()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    elif user_input.lower() == '/results':
                        self._show_results()
                        self.console.print()
                        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
                        continue

                    # Send query to AI
                    self._send_query(user_input, context_files, run_in_background=run_in_bg)

                except KeyboardInterrupt:
                    self.console.print()
                    action = questionary.select(
                        "What would you like to do?",
                        choices=[
                            "Continue in Browser",
                            "Switch to another menu",
                            "Exit to Dashboard"
                        ],
                        style=questionary.Style([
                            ('selected', 'fg:cyan bold'),
                            ('pointer', 'fg:cyan bold'),
                        ])
                    ).ask()

                    if action == "Switch to another menu":
                        menu_choice = self._show_menu_navigation()
                        if menu_choice:
                            return menu_choice
                    elif action == "Exit to Dashboard":
                        return None
                    # Otherwise continue in Browser
                    continue

                except Exception as e:
                    self.console.print(f"[red]Error: {str(e)}[/red]")
                    continue

        except Exception as e:
            self.console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
            self.console.input("\nPress Enter to continue...")
            return None

    def _send_query(self, prompt: str, context_files: Optional[List[str]] = None, run_in_background: bool = False):
        """Send query to AI and display response

        Args:
            prompt: User's question/prompt
            context_files: Optional list of files for context
            run_in_background: If True, run in background without waiting
        """
        # Prepend system context on first message if system-aware mode
        full_prompt = prompt
        if self.system_aware and not self.system_context_sent:
            system_context = SystemContextProvider.get_contextualized_prompt()
            full_prompt = f"{system_context}\n\n---\n\nUser: {prompt}"
            self.system_context_sent = True

        # Store original prompt in history
        self.conversation_history.append({
            'role': 'user',
            'content': prompt,
            'timestamp': time.time()
        })

        # Create background task
        def query_task():
            return self.service.query(
                prompt=full_prompt,
                tool=self.tool,
                files=context_files,
                working_dir=self.working_dir
            )

        # Start background task
        task_id = task_manager.create_task(
            description=f"{prompt[:50]}{'...' if len(prompt) > 50 else ''}",
            func=query_task
        )

        if run_in_background:
            # Just start and return
            self.console.print(f"\n[bold green]✓ Task started in background[/bold green] [dim](ID: {task_id})[/dim]")
            self.console.print(f"[dim]Continue working. Use /results to view when complete.[/dim]\n")
            return

        # Wait for completion with option to detach
        self.console.print(f"\n[bold cyan]🤔 {self.service.get_tool_info(self.tool)['name']} is thinking...[/bold cyan]")
        self.console.print(f"[dim]Waiting for response... Type 'bg' then Enter to send to background[/dim]\n")

        # Poll for completion
        try:
            while True:
                task = task_manager.get_task(task_id)
                if task and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    break
                time.sleep(0.3)

            # Get result
            task = task_manager.get_task(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                response = task.result

                # Store in history
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': time.time()
                })

                # Display response
                self.console.print()
                self.console.print(Panel(
                    Markdown(response) if self._is_markdown(response) else Text(response),
                    title=f"[bold cyan]🤖 {self.service.get_tool_info(self.tool)['name']}[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2)
                ))

                # Execute commands if system-aware
                if self.system_aware:
                    self._execute_commands_from_response(response)

                # Pause before returning to menu (like web viewer)
                self.console.print()
                questionary.press_any_key_to_continue("\nPress any key to continue...").ask()

            elif task and task.status == TaskStatus.FAILED:
                self.console.print(Panel(
                    f"[red]Error: {task.error}[/red]",
                    title="AI Error",
                    border_style="red"
                ))
                self.console.print()
                questionary.press_any_key_to_continue("\nPress any key to continue...").ask()

        except KeyboardInterrupt:
            # Task continues in background
            self.console.print(f"\n\n[bold green]✓ Sent to background[/bold green] [dim](Task {task_id} still running)[/dim]")
            self.console.print(f"[dim]Use /results to view when complete[/dim]\n")
            return

    def _execute_commands_from_response(self, response: str):
        """Extract and execute commands from AI response

        Args:
            response: AI response text
        """
        commands = SystemExecutor.extract_commands(response)

        if not commands:
            return

        self.console.print()
        self.console.print(f"[bold yellow]⚡ Found {len(commands)} command(s) to execute[/bold yellow]")

        for i, command in enumerate(commands, 1):
            action = command.get('action', 'UNKNOWN')

            # Show command details
            self.console.print()
            self.console.print(Panel(
                f"[bold]Action:[/bold] {action}\n" +
                f"[bold]Parameters:[/bold]\n" +
                "\n".join(f"  • {k}: {v}" for k, v in command.get('params', {}).items()),
                title=f"[cyan]Command {i}/{len(commands)}[/cyan]",
                border_style="yellow"
            ))

            # Ask for confirmation
            execute = questionary.confirm(
                f"Execute this {action} command?",
                default=True
            ).ask()

            if execute:
                with self.console.status(f"[yellow]Executing {action}...[/yellow]", spinner="dots"):
                    success, message, result = SystemExecutor.execute_command(command)

                if success:
                    self.console.print(f"[green]{message}[/green]")

                    # Show result details if available
                    if result:
                        if isinstance(result, dict):
                            result_text = "\n".join(f"  • {k}: {v}" for k, v in result.items())
                        elif isinstance(result, list):
                            result_text = f"  • {len(result)} items returned"
                            if result and len(result) <= 5:
                                for item in result:
                                    if isinstance(item, dict):
                                        result_text += f"\n    - {item.get('name') or item.get('title') or str(item)}"
                        else:
                            result_text = str(result)

                        self.console.print(Panel(
                            result_text,
                            title="[green]Result[/green]",
                            border_style="green"
                        ))
                else:
                    self.console.print(f"[red]✗ {message}[/red]")
            else:
                self.console.print("[dim]Command skipped[/dim]")

    def _show_help(self):
        """Display help information"""
        help_table = Table(title="AI Assistant Commands & Shortcuts", show_header=True, header_style="bold cyan")
        help_table.add_column("Key/Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")

        commands = [
            ("", "[bold yellow]Single Key Actions[/]"),
            ("1-9, 0", "Instant menu navigation (no Enter)"),
            ("?", "Show this help"),
            ("q", "Quick exit from AI Assistant"),
            ("Enter", "Start typing AI query"),
            ("", ""),
            ("", "[bold yellow]Slash Commands[/]"),
            ("/help", "Show this help message"),
            ("/bg <prompt>", "Run query in background immediately"),
            ("/context", "Add files as context for the AI"),
            ("/clear", "Clear conversation history"),
            ("/history", "Show conversation history"),
            ("/status", "Show AI tool status"),
            ("/tasks", "Show running background tasks"),
            ("/results", "View completed task results"),
            ("/menu", "Show menu selection dialog"),
            ("/exit, /quit, /q", "Exit AI Assistant"),
            ("", ""),
            ("Ctrl+C while waiting", "Send current query to background"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)

    def _show_menu_navigation(self) -> Optional[str]:
        """Show menu navigation options and return selected menu

        Returns:
            Selected menu name or None if cancelled
        """
        menu_options = [
            "Dashboard",
            "Profiles",
            "Companies",
            "Network & Relationships",
            "Tags",
            "Search",
            "Workshop",
            "Tasks",
            "Goals",
            "Import/Export",
            "AI CLI Control",
            "← Stay in Browser",
        ]

        choice = questionary.select(
            "Switch to which menu?",
            choices=menu_options,
            style=questionary.Style([
                ('selected', 'fg:cyan bold'),
                ('pointer', 'fg:cyan bold'),
                ('question', 'fg:cyan bold'),
            ])
        ).ask()

        if choice and choice != "← Stay in Browser":
            return choice
        return None

    def _add_context_files(self) -> List[str]:
        """Add files as context for AI queries

        Returns:
            List of file paths to include
        """
        self.console.print("\n[bold]Add Context Files[/bold]")
        self.console.print("Enter file paths (one per line, empty line to finish):")

        files = []
        while True:
            file_path = Prompt.ask(
                f"[dim]File {len(files) + 1}[/dim]",
                default="",
                console=self.console
            ).strip()

            if not file_path:
                break

            # Resolve path
            path = Path(file_path)
            if not path.is_absolute():
                path = Path(self.working_dir) / path

            if path.exists() and path.is_file():
                files.append(str(path))
                self.console.print(f"[green]✓[/green] Added: {path}")
            else:
                self.console.print(f"[red]✗[/red] File not found: {path}")

        if files:
            self.console.print(f"\n[green]Added {len(files)} file(s) as context[/green]")
        else:
            self.console.print("[dim]No files added[/dim]")

        return files

    def _show_history(self):
        """Display conversation history"""
        if not self.conversation_history:
            self.console.print("[dim]No conversation history yet[/dim]")
            return

        self.console.print("\n[bold]Conversation History[/bold]\n")

        for i, entry in enumerate(self.conversation_history, 1):
            role = entry['role']
            content = entry['content']
            timestamp = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))

            if role == 'user':
                self.console.print(f"[bold green][{timestamp}] You:[/bold green] {content}")
            else:
                # Truncate long responses
                display_content = content[:200] + "..." if len(content) > 200 else content
                self.console.print(f"[bold cyan][{timestamp}] AI:[/bold cyan] {display_content}")

            if i < len(self.conversation_history):
                self.console.print()

    def _show_status(self):
        """Show AI tool status"""
        health = self.service.check_health()

        status_table = Table(title="AI Tools Status", show_header=True, header_style="bold cyan")
        status_table.add_column("Tool", style="cyan", width=20)
        status_table.add_column("Status", style="white", width=15)
        status_table.add_column("Command", style="dim", width=15)

        all_tools = self.service.get_installed_tools()
        for tool in all_tools:
            status = "✓ Installed" if tool['installed'] else "✗ Not installed"
            style = "green" if tool['installed'] else "red"
            status_table.add_row(
                tool['name'],
                f"[{style}]{status}[/{style}]",
                tool['command']
            )

        self.console.print(status_table)
        self.console.print(f"\n[bold]Current Tool:[/bold] {self.service.get_tool_info(self.tool)['name']}")
        self.console.print(f"[bold]Working Directory:[/bold] {self.working_dir}")

    def _show_background_tasks(self):
        """Show running background tasks"""
        running_tasks = task_manager.get_running_tasks()

        if not running_tasks:
            self.console.print("[dim]No background tasks running[/dim]")
            return

        task_table = Table(title="Background Tasks", show_header=True, header_style="bold cyan")
        task_table.add_column("ID", style="cyan", width=10)
        task_table.add_column("Description", style="white", width=40)
        task_table.add_column("Status", style="white", width=10)
        task_table.add_column("Started", style="dim", width=15)

        for task in running_tasks:
            status_icon = "🔄" if task.status == TaskStatus.RUNNING else "⏳"
            elapsed = (datetime.now() - task.started_at).total_seconds()
            task_table.add_row(
                task.task_id,
                task.description[:40],
                f"{status_icon} {task.status.value}",
                f"{int(elapsed)}s ago"
            )

        self.console.print(task_table)

    def _show_results(self):
        """Show and display completed task results"""
        completed_tasks = task_manager.get_completed_tasks()

        if not completed_tasks:
            self.console.print("[dim]No completed results available[/dim]")
            return

        # Show list of completed tasks
        self.console.print("\n[bold]Completed Tasks:[/bold]\n")
        for i, task in enumerate(completed_tasks, 1):
            elapsed = (task.completed_at - task.started_at).total_seconds()
            self.console.print(f"[cyan]{i}.[/cyan] {task.description} [dim]({elapsed:.1f}s)[/dim]")

        self.console.print()
        choice = Prompt.ask(
            "View result number (or press Enter to skip)",
            default="",
            console=self.console
        )

        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(completed_tasks):
                task = completed_tasks[idx]

                # Display result
                self.console.print()
                self.console.print(Panel(
                    Markdown(task.result) if self._is_markdown(task.result) else Text(str(task.result)),
                    title=f"[bold cyan]Result: {task.description}[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2)
                ))

                # Ask to execute commands if system-aware
                if self.system_aware:
                    execute = questionary.confirm(
                        "Execute any commands in this result?",
                        default=False
                    ).ask()
                    if execute:
                        self._execute_commands_from_response(task.result)

    def _is_markdown(self, text: str) -> bool:
        """Check if text appears to be markdown

        Args:
            text: Text to check

        Returns:
            True if text looks like markdown
        """
        markdown_indicators = ['```', '##', '**', '- ', '* ', '1. ', '[', ']', '(', ')']
        return any(indicator in text for indicator in markdown_indicators)


class AIAssistantMenu:
    """AI Assistant menu for the TUI"""

    # Store active sessions per tool
    _active_sessions: Dict[str, 'InteractiveAISession'] = {}

    def __init__(self):
        """Initialize AI assistant menu"""
        self.console = Console()
        self.service = AICLIService()

    def show(self) -> Optional[str]:
        """Show AI assistant menu

        Returns:
            Menu name to navigate to, or None to return to previous menu
        """
        while True:
            # Get installed tools
            installed_tools = self.service.get_installed_tools()
            installed = [t for t in installed_tools if t['installed']]

            # Build menu choices
            choices = []

            if installed:
                # Check if Claude Code is installed
                has_claude = any(t['id'] == 'claude' and t['installed'] for t in installed_tools)

                if has_claude:
                    choices.append("🚀 Native Claude Code (Full Features)")

                choices.append("💬 Quick Ask (one question)")
                choices.append("🔄 Start Interactive Session")
                choices.append("📊 View AI Tools Status")
                choices.append("ℹ️  Help & Setup Guide")
            else:
                choices.append("⚠️  No AI Tools Installed - View Setup Guide")

            choices.append("← Back to Main Menu")

            # Show menu
            choice = questionary.select(
                "Browser",
                choices=choices,
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                    ('question', 'fg:cyan bold'),
                ])
            ).ask()

            if choice == "← Back to Main Menu":
                return None

            elif choice == "🚀 Native Claude Code (Full Features)":
                menu_choice = self._launch_native_claude_code()
                if menu_choice:
                    return menu_choice

            elif choice == "💬 Quick Ask (one question)":
                self._quick_ask(installed)

            elif choice == "🔄 Start Interactive Session":
                menu_choice = self._start_interactive_session(installed)
                if menu_choice:
                    return menu_choice

            elif choice == "📊 View AI Tools Status":
                self._show_status()

            elif choice in ["ℹ️  Help & Setup Guide", "⚠️  No AI Tools Installed - View Setup Guide"]:
                self._show_setup_guide()

    def _launch_native_claude_code(self) -> Optional[str]:
        """Launch native Claude Code CLI with full features

        Returns:
            Menu name to navigate to, or None to stay
        """
        import os
        import tempfile
        from pathlib import Path

        self.console.clear()
        self.console.print(Panel(
            "[bold cyan]🚀 Native Claude Code Integration[/bold cyan]\n\n"
            "This will launch the full Claude Code CLI with all its native features:\n"
            "• File editing and code generation\n"
            "• Multi-step reasoning and planning\n"
            "• Full codebase analysis\n"
            "• Native tool usage\n"
            "• All Claude Code commands\n\n"
            "[yellow]You'll have full access to Claude Code's capabilities.[/yellow]",
            border_style="cyan"
        ))
        self.console.print()

        # Ask about LeadSauce context
        include_context = questionary.confirm(
            "Include LeadSauce system context? (Provides info about the CRM)",
            default=True
        ).ask()

        if include_context is None:
            return None

        # Prepare launch
        self.console.print("\n[bold cyan]Launching Claude Code...[/bold cyan]")
        self.console.print("[dim]Press Ctrl+D or type 'exit' in Claude Code to return to LeadSauce[/dim]\n")

        # Build command
        cmd_parts = ["claude"]

        # If context requested, create a context file
        context_file = None
        if include_context:
            try:
                from leadsauce.services.system_context import SystemContextProvider

                # Create temporary context file
                context_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, prefix='leadsauce_context_')
                context_file.write(f"""# LeadSauce System Context

You are working with LeadSauce CLI, a professional network management system.

## System Information

{SystemContextProvider.get_contextualized_prompt()}

## Working Directory
{Path.cwd()}

## Note
You have full access to all Claude Code features. You can:
- Edit files in the LeadSauce codebase
- Search and analyze code
- Create new features
- Debug issues
- Use all native Claude Code commands

When you're done, press Ctrl+D or type 'exit' to return to the LeadSauce menu.
""")
                context_file.close()

                # Add context file to command
                cmd_parts.extend(["--file", context_file.name])

            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not create context file: {e}[/yellow]")

        # Launch Claude Code
        cmd = " ".join(cmd_parts)

        try:
            # Use os.system for full interactive experience
            self.console.print(f"[dim]Running: {cmd}[/dim]\n")
            time.sleep(1)  # Brief pause before launch

            exit_code = os.system(cmd)

            # Clean up context file
            if context_file:
                try:
                    os.unlink(context_file.name)
                except:
                    pass

            # Show return message
            self.console.print("\n[green]✓ Returned from Claude Code[/green]")
            self.console.print()

            # Ask what to do next
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "Return to Browser menu",
                    "Switch to another menu",
                    "Launch Claude Code again"
                ],
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                ])
            ).ask()

            if action == "Switch to another menu":
                # Import here to avoid circular import
                from leadsauce.utils.ai_interactive import InteractiveAISession
                session = InteractiveAISession(tool='claude')
                return session._show_menu_navigation()
            elif action == "Launch Claude Code again":
                return self._launch_native_claude_code()

            return None

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Interrupted[/yellow]")
            return None
        except Exception as e:
            self.console.print(f"\n[red]Error launching Claude Code: {e}[/red]")
            self.console.print("[yellow]Make sure Claude Code is installed: npm install -g @anthropic-ai/claude-code[/yellow]")
            self.console.input("\nPress Enter to continue...")
            return None

    def _quick_ask(self, installed_tools: List[Dict]):
        """Quick ask mode - single question

        Args:
            installed_tools: List of installed AI tools
        """
        # Select tool
        if len(installed_tools) == 1:
            tool = installed_tools[0]['id']
        else:
            tool_choice = questionary.select(
                "Select AI tool:",
                choices=[f"{t['name']} ({t['command']})" for t in installed_tools]
            ).ask()
            tool = next(t['id'] for t in installed_tools if t['name'] in tool_choice)

        # Get question
        question = questionary.text(
            "What's your question?",
            multiline=False
        ).ask()

        if not question:
            return

        # Process
        console = Console()
        with console.status(f"[bold cyan]Asking {self.service.get_tool_info(tool)['name']}...[/bold cyan]", spinner="dots"):
            try:
                response = self.service.query(prompt=question, tool=tool)

                console.print("\n")
                console.print(Panel(
                    Markdown(response) if '```' in response or '##' in response else Text(response),
                    title=f"[bold cyan]🤖 {self.service.get_tool_info(tool)['name']}[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2)
                ))

            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")

        console.input("\nPress Enter to continue...")

    def _start_interactive_session(self, installed_tools: List[Dict]) -> Optional[str]:
        """Start interactive AI session

        Args:
            installed_tools: List of installed AI tools

        Returns:
            Menu name to navigate to, or None to stay
        """
        # Select tool
        if len(installed_tools) == 1:
            tool = installed_tools[0]['id']
        else:
            tool_choice = questionary.select(
                "Select AI tool:",
                choices=[f"{t['name']} ({t['command']})" for t in installed_tools]
            ).ask()

            if not tool_choice:
                return None

            tool = next(t['id'] for t in installed_tools if t['name'] in tool_choice)

        # Check if session already exists for this tool
        if tool in self._active_sessions:
            session = self._active_sessions[tool]
            history_count = len(session.conversation_history)
            running_tasks = len(task_manager.get_running_tasks())

            self.console.print(f"\n[bold cyan]Found existing session![/bold cyan]")
            self.console.print(f"  • {history_count} messages in history")
            if running_tasks > 0:
                self.console.print(f"  • {running_tasks} task(s) running in background")
            self.console.print()

            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "Resume existing session",
                    "Start fresh session (clears history)",
                    "← Back"
                ],
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                ])
            ).ask()

            if action == "← Back":
                return None
            elif action == "Start fresh session (clears history)":
                # Create new session
                session = InteractiveAISession(tool=tool)
                self._active_sessions[tool] = session
            # else: resume existing session (already assigned)
        else:
            # Create new session
            session = InteractiveAISession(tool=tool)
            self._active_sessions[tool] = session

        return session.run()

    def _show_status(self):
        """Show AI tools status"""
        all_tools = self.service.get_installed_tools()

        status_table = Table(title="AI Tools Status", show_header=True, header_style="bold cyan")
        status_table.add_column("Tool", style="cyan", width=25)
        status_table.add_column("Status", style="white", width=20)
        status_table.add_column("Command", style="dim", width=15)

        for tool in all_tools:
            status = "✓ Installed" if tool['installed'] else "✗ Not installed"
            style = "green" if tool['installed'] else "red"
            status_table.add_row(
                tool['name'],
                f"[{style}]{status}[/{style}]",
                tool['command']
            )

        self.console.print("\n")
        self.console.print(status_table)
        self.console.input("\nPress Enter to continue...")

    def _show_setup_guide(self):
        """Show setup guide for AI tools"""
        guide = """
# 🤖 AI Assistant Setup Guide

## Supported AI Tools

LeadSauce integrates with popular AI coding assistants:

### 1. Claude Code (Anthropic)
**Installation:**
```bash
npm install -g @anthropic-ai/claude-code
```

**Requirements:**
- Node.js installed
- Paid Claude.ai subscription

**Features:**
- Excellent code understanding
- Best for Python development
- Supports MCP for extensibility

### 2. Codex CLI (OpenAI)
**Installation:**
```bash
# Follow instructions at: https://github.com/openai/codex
# Requires ChatGPT Plus/Pro/Team/Enterprise
```

**Features:**
- GitHub integration
- PR creation from CLI
- Multiple approval modes

### 3. Aider (Open Source)
**Installation:**
```bash
pip install aider-chat
```

**Requirements:**
- OpenAI API key (set OPENAI_API_KEY env variable)
- Or use local models with --model flag

**Features:**
- Open source
- Git integration
- Supports multiple LLM backends

## After Installation

1. Install your preferred AI tool
2. Return to this menu
3. Select "Start Interactive Session"
4. Start asking questions!

## Tips

- **Be specific:** The more context you provide, the better the answers
- **Use /context:** Add relevant files for better understanding
- **Interactive mode:** Use for back-and-forth conversations
- **Quick ask:** Use for simple, one-off questions
        """

        self.console.print(Panel(
            Markdown(guide),
            title="[bold cyan]AI Assistant Setup[/bold cyan]",
            border_style="cyan"
        ))
        self.console.input("\nPress Enter to continue...")
