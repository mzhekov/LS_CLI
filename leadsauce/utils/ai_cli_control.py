"""AI CLI Control - Direct system control via AI CLI tools

This module provides a direct control interface where AI CLI tools (Claude Code, Codex, etc.)
can operate the LeadSauce system autonomously, executing operations in real-time.

This is different from the AI Assistant which is conversational. AI CLI Control allows
AI tools to directly manage the system with minimal user intervention.
"""

import time
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.columns import Columns
import questionary

from leadsauce.services.ai_cli import AICLIService, ToolNotInstalledError, ToolTimeoutError, AICLIError
from leadsauce.services.system_context import SystemContextProvider
from leadsauce.services.system_executor import SystemExecutor
from leadsauce.utils.db import get_session


class AICLIControlSession:
    """AI CLI Control session - Direct system control via AI"""

    def __init__(self, tool: str = 'claude', auto_execute: bool = False):
        """Initialize AI CLI Control session

        Args:
            tool: AI CLI tool to use
            auto_execute: If True, execute commands automatically without confirmation
        """
        self.tool = tool
        self.auto_execute = auto_execute
        self.console = Console()
        self.service = AICLIService(default_tool=tool)
        self.command_log: List[Dict] = []
        self.working_dir = str(Path.cwd())
        self.session_start = datetime.now()

    def show_control_panel(self):
        """Display the AI CLI Control panel"""
        tool_info = self.service.get_tool_info(self.tool)
        stats = SystemContextProvider.get_current_stats()
        session_duration = datetime.now() - self.session_start

        control_text = f"""
# 🎮 AI CLI Control - {tool_info['name']}

**Session Mode:** {'🤖 Auto-Execute (AI has control)' if self.auto_execute else '✋ Manual Approval (You have control)'}

## System Status
- **Profiles:** {stats['profile_count']}
- **Companies:** {stats['company_count']}
- **Active Reminders:** {stats['reminder_count']}
- **Tags:** {stats['tag_count']}

## Session Info
- **Duration:** {str(session_duration).split('.')[0]}
- **Commands Executed:** {len(self.command_log)}
- **Working Directory:** `{self.working_dir}`

## What AI Can Do
The AI has **direct control** over your LeadSauce system:
- ✅ Create, update, delete profiles and companies
- ✅ Manage reminders and tasks
- ✅ Log interactions and relationships
- ✅ Search and analyze data
- ✅ Execute multiple operations in sequence

## Control Mode
{'⚠️  **AUTO-EXECUTE MODE**: AI executes commands automatically!' if self.auto_execute else '✓ **MANUAL MODE**: You approve each command before execution'}

**Commands:**
- Natural language: "Create 5 test contacts for TechCorp"
- Type `/help` for all commands
- Type `/menu` to switch to another section
- Type `/mode` to toggle auto-execute
- Type `/log` to view command history
- Type `/exit` to leave control mode
        """

        self.console.print(Panel(
            Markdown(control_text),
            title="[bold cyan]🎮 AI CLI Control[/bold cyan]",
            border_style="cyan" if not self.auto_execute else "yellow"
        ))

    def run(self) -> Optional[str]:
        """Run the AI CLI Control session

        Returns:
            Menu name to navigate to, or None to return to previous menu
        """
        try:
            # Check if tool is installed
            if not self.service.is_installed(self.tool):
                tool_info = self.service.get_tool_info(self.tool)
                self.console.print(Panel(
                    f"[bold red]❌ {tool_info['name']} is not installed[/bold red]\n\n"
                    f"To use AI CLI Control, please install:\n"
                    f"[cyan]{tool_info['install_cmd']}[/cyan]",
                    title="Installation Required",
                    border_style="red"
                ))
                self.console.input("\nPress Enter to continue...")
                return None

            self.console.clear()
            self.show_control_panel()

            # Send initial system context
            initial_prompt = self._build_control_prompt()

            while True:
                try:
                    self.console.print()
                    user_input = Prompt.ask(
                        "[bold green]Command[/bold green]",
                        console=self.console
                    ).strip()

                    if not user_input:
                        continue

                    # Handle control commands
                    if user_input.lower() in ['/exit', '/quit', '/q']:
                        self._show_session_summary()
                        return None

                    elif user_input.lower() == '/help':
                        self._show_control_help()
                        continue

                    elif user_input.lower() == '/menu':
                        menu_choice = self._show_menu_navigation()
                        if menu_choice:
                            self.console.print(f"[dim]Switching to {menu_choice}...[/dim]")
                            return menu_choice
                        continue

                    elif user_input.lower() == '/mode':
                        self._toggle_mode()
                        self.console.clear()
                        self.show_control_panel()
                        continue

                    elif user_input.lower() == '/log':
                        self._show_command_log()
                        continue

                    elif user_input.lower() == '/stats':
                        self._show_system_stats()
                        continue

                    elif user_input.lower() == '/clear':
                        self.console.clear()
                        self.show_control_panel()
                        continue

                    # Process AI command
                    full_prompt = f"{initial_prompt}\n\n---\n\nUser Command: {user_input}"
                    self._process_command(full_prompt)

                except KeyboardInterrupt:
                    self.console.print()
                    action = questionary.select(
                        "What would you like to do?",
                        choices=[
                            "Continue in AI CLI Control",
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
                    # Otherwise continue in AI CLI Control
                    continue

                except Exception as e:
                    self.console.print(f"[red]Error: {str(e)}[/red]")
                    continue

        except Exception as e:
            self.console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
            self.console.input("\nPress Enter to continue...")
            return None

    def _build_control_prompt(self) -> str:
        """Build the control prompt for AI

        Returns:
            System prompt with control instructions
        """
        context = SystemContextProvider.get_contextualized_prompt()

        control_instructions = """

## AI CLI CONTROL MODE

You are in CONTROL MODE. This means:

1. **Direct Execution**: Your commands will be executed directly in the LeadSauce system
2. **Multiple Operations**: You can perform multiple operations in sequence
3. **Autonomous Operation**: Execute operations to fulfill user requests completely
4. **JSON Commands**: Use the JSON format from the system context to execute operations

## Expected Behavior

When the user gives you a command like:
- "Create 5 test contacts for Microsoft"
- "Add reminders for all my meetings next week"
- "Find all profiles without email and flag them"

You should:
1. Generate ALL necessary JSON commands to complete the task
2. Execute them in the correct sequence
3. Provide status updates
4. Report completion with summary

## Example

User: "Create 3 test profiles for TechCorp"

You respond with:
"I'll create 3 test profiles for TechCorp with realistic data."

```json
{
  "action": "CREATE_PROFILE",
  "params": {
    "name": "John Smith",
    "company_name": "TechCorp",
    "title": "Software Engineer",
    "email": "john.smith@techcorp.com"
  }
}
```

```json
{
  "action": "CREATE_PROFILE",
  "params": {
    "name": "Sarah Johnson",
    "company_name": "TechCorp",
    "title": "Product Manager",
    "email": "sarah.johnson@techcorp.com"
  }
}
```

```json
{
  "action": "CREATE_PROFILE",
  "params": {
    "name": "Mike Davis",
    "company_name": "TechCorp",
    "title": "Senior Developer",
    "email": "mike.davis@techcorp.com"
  }
}
```

"Completed! Created 3 profiles for TechCorp."

## Remember
- Always use JSON commands for operations
- Provide clear status updates
- Complete the full task, not just first step
- Handle errors gracefully
"""

        return context + control_instructions

    def _process_command(self, prompt: str):
        """Process AI command and execute

        Args:
            prompt: Full prompt with context and user command
        """
        try:
            # Query AI with status display
            with self.console.status(
                f"[bold cyan]{self.service.get_tool_info(self.tool)['name']} processing... [dim](Press Ctrl+C to cancel)[/dim][/bold cyan]",
                spinner="dots"
            ):
                response = self.service.query(
                    prompt=prompt,
                    tool=self.tool,
                    working_dir=self.working_dir
                )

            # Display AI response (outside status context)
            self.console.print()
            self.console.print(Panel(
                Markdown(response) if '```' in response else Text(response),
                title=f"[bold cyan]🤖 AI Response[/bold cyan]",
                border_style="cyan"
            ))

            # Extract and execute commands (outside status context)
            self._execute_commands_from_response(response)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled[/yellow]")
            self.console.print("[dim]Returning to prompt... (type /menu to switch sections or /exit to quit)[/dim]")
            raise  # Re-raise to be caught by outer handler

        except (ToolNotInstalledError, ToolTimeoutError, AICLIError) as e:
            self.console.print(Panel(
                f"[red]{str(e)}[/red]",
                title="Error",
                border_style="red"
            ))

    def _execute_commands_from_response(self, response: str):
        """Extract and execute commands from AI response

        Args:
            response: AI response text
        """
        commands = SystemExecutor.extract_commands(response)

        if not commands:
            return

        self.console.print()
        self.console.print(f"[bold yellow]⚡ Found {len(commands)} command(s)[/bold yellow]")

        for i, command in enumerate(commands, 1):
            action = command.get('action', 'UNKNOWN')

            # Show command
            self.console.print()
            self.console.print(Panel(
                f"[bold]Action:[/bold] {action}\n" +
                f"[bold]Parameters:[/bold]\n" +
                "\n".join(f"  • {k}: {v}" for k, v in command.get('params', {}).items()),
                title=f"[cyan]Command {i}/{len(commands)}[/cyan]",
                border_style="yellow"
            ))

            # Execute based on mode
            should_execute = self.auto_execute

            if not self.auto_execute:
                should_execute = questionary.confirm(
                    f"Execute {action}?",
                    default=True
                ).ask()

            if should_execute:
                with self.console.status(f"[yellow]Executing {action}...[/yellow]", spinner="dots"):
                    success, message, result = SystemExecutor.execute_command(command)

                # Log command
                self.command_log.append({
                    'timestamp': datetime.now(),
                    'action': action,
                    'success': success,
                    'message': message
                })

                if success:
                    self.console.print(f"[green]✓ {message}[/green]")

                    if result:
                        if isinstance(result, dict):
                            result_text = "\n".join(f"  • {k}: {v}" for k, v in result.items())
                        elif isinstance(result, list):
                            result_text = f"  • {len(result)} items"
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

    def _toggle_mode(self):
        """Toggle between auto-execute and manual mode"""
        self.auto_execute = not self.auto_execute

        if self.auto_execute:
            confirm = questionary.confirm(
                "⚠️  Enable AUTO-EXECUTE mode? AI will execute commands without confirmation!",
                default=False
            ).ask()

            if not confirm:
                self.auto_execute = False
                self.console.print("[yellow]Staying in MANUAL mode[/yellow]")
            else:
                self.console.print("[bold yellow]⚠️  AUTO-EXECUTE ENABLED[/bold yellow]")
        else:
            self.console.print("[green]✓ MANUAL mode enabled[/green]")

    def _show_control_help(self):
        """Display control help"""
        help_table = Table(title="AI CLI Control Commands", show_header=True, header_style="bold cyan")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help"),
            ("/mode", "Toggle auto-execute mode"),
            ("/log", "View command execution log"),
            ("/stats", "Show system statistics"),
            ("/clear", "Clear screen and refresh"),
            ("/menu", "Switch to another main menu"),
            ("/exit, /quit, /q", "Exit AI CLI Control"),
            ("Natural language", "Give AI commands to execute"),
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
            "Browser",
            "AI Assistant",
            "← Stay in AI CLI Control",
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

        if choice and choice != "← Stay in AI CLI Control":
            return choice
        return None

    def _show_command_log(self):
        """Display command execution log"""
        if not self.command_log:
            self.console.print("[dim]No commands executed yet[/dim]")
            return

        log_table = Table(title="Command Execution Log", show_header=True, header_style="bold cyan")
        log_table.add_column("Time", style="dim", width=12)
        log_table.add_column("Action", style="cyan", width=25)
        log_table.add_column("Status", style="white", width=10)
        log_table.add_column("Message", style="white")

        for entry in self.command_log[-20:]:  # Last 20 commands
            timestamp = entry['timestamp'].strftime('%H:%M:%S')
            status = "[green]✓[/green]" if entry['success'] else "[red]✗[/red]"
            log_table.add_row(
                timestamp,
                entry['action'],
                status,
                entry['message'][:50] + "..." if len(entry['message']) > 50 else entry['message']
            )

        self.console.print(log_table)

    def _show_system_stats(self):
        """Display current system statistics"""
        stats = SystemContextProvider.get_current_stats()

        stats_table = Table(title="System Statistics", show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="cyan", width=25)
        stats_table.add_column("Count", style="green", justify="right", width=15)

        stats_table.add_row("👥 Profiles", str(stats['profile_count']))
        stats_table.add_row("🏢 Companies", str(stats['company_count']))
        stats_table.add_row("⏰ Active Reminders", str(stats['reminder_count']))
        stats_table.add_row("🏷️  Tags", str(stats['tag_count']))

        self.console.print(stats_table)

    def _show_session_summary(self):
        """Display session summary"""
        duration = datetime.now() - self.session_start
        success_count = sum(1 for log in self.command_log if log['success'])
        fail_count = len(self.command_log) - success_count

        summary = f"""
## Session Summary

- **Duration:** {str(duration).split('.')[0]}
- **Total Commands:** {len(self.command_log)}
- **Successful:** {success_count}
- **Failed:** {fail_count}
- **Mode:** {'Auto-Execute' if self.auto_execute else 'Manual'}

Thank you for using AI CLI Control!
        """

        self.console.print(Panel(
            Markdown(summary),
            title="[bold cyan]Session Complete[/bold cyan]",
            border_style="cyan"
        ))


class AICLIControlMenu:
    """AI CLI Control menu"""

    def __init__(self):
        """Initialize AI CLI Control menu"""
        self.console = Console()
        self.service = AICLIService()

    def show(self) -> Optional[str]:
        """Show AI CLI Control menu

        Returns:
            Menu name to navigate to, or None to return to previous menu
        """
        while True:
            self.console.clear()

            # Get installed tools
            installed_tools = self.service.get_installed_tools()
            installed = [t for t in installed_tools if t['installed']]

            # Header
            self.console.print(Panel(
                "[bold cyan]🎮 AI CLI Control[/bold cyan]\n\n"
                "Give AI **direct control** over your LeadSauce system.\n"
                "AI can autonomously execute operations to fulfill your requests.\n\n"
                "[yellow]⚠️  This is different from AI Assistant:[/yellow]\n"
                "• AI Assistant (0): Conversational help and advice\n"
                "• AI CLI Control (9): Direct system control and automation",
                border_style="cyan"
            ))
            self.console.print()

            if not installed:
                self.console.print(Panel(
                    "[bold red]No AI CLI tools installed[/bold red]\n\n"
                    "Please install at least one AI CLI tool:\n"
                    "• Claude Code: npm install -g @anthropic-ai/claude-code\n"
                    "• Codex CLI: https://github.com/openai/codex\n"
                    "• Aider: pip install aider-chat",
                    title="⚠️  Setup Required",
                    border_style="red"
                ))
                self.console.input("\nPress Enter to continue...")
                return None

            # Build menu choices
            choices = []

            # Check if Claude Code is installed
            has_claude = any(t['id'] == 'claude' and t['installed'] for t in installed_tools)

            if has_claude:
                choices.append("🚀 Native Claude Code (Full Features)")

            if len(installed) == 1:
                tool = installed[0]
                choices.append(f"🤖 Start Control Session with {tool['name']}")
            else:
                for tool in installed:
                    choices.append(f"🤖 Start Control Session with {tool['name']}")

            choices.extend([
                "📊 View AI Tools Status",
                "ℹ️  About AI CLI Control",
                "← Back to Main Menu"
            ])

            choice = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                ])
            ).ask()

            if not choice or "Back to Main Menu" in choice:
                return None

            elif choice == "🚀 Native Claude Code (Full Features)":
                menu_choice = self._launch_native_claude_code()
                if menu_choice:
                    return menu_choice

            elif "Start Control Session" in choice:
                # Extract tool name
                tool = None
                for t in installed:
                    if t['name'] in choice:
                        tool = t['id']
                        break

                if tool:
                    # Ask about mode
                    mode = questionary.select(
                        "Choose control mode:",
                        choices=[
                            "✋ Manual Mode (You approve each command)",
                            "🤖 Auto-Execute Mode (AI executes automatically)"
                        ]
                    ).ask()

                    auto_execute = "Auto-Execute" in mode if mode else False

                    # Start session
                    session = AICLIControlSession(tool=tool, auto_execute=auto_execute)
                    menu_choice = session.run()
                    if menu_choice:
                        return menu_choice

            elif "View AI Tools Status" in choice:
                self._show_status()

            elif "About AI CLI Control" in choice:
                self._show_about()

    def _launch_native_claude_code(self) -> Optional[str]:
        """Launch native Claude Code CLI with full features

        Returns:
            Menu name to navigate to, or None to stay
        """
        import os
        import tempfile
        import time
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
                    "Return to AI CLI Control menu",
                    "Switch to another menu",
                    "Launch Claude Code again"
                ],
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                ])
            ).ask()

            if action == "Switch to another menu":
                return self._show_menu_navigation_from_menu()
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

    def _show_menu_navigation_from_menu(self) -> Optional[str]:
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
            "Browser",
            "AI Assistant",
            "← Stay in AI CLI Control",
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

        if choice and choice != "← Stay in AI CLI Control":
            return choice
        return None

    def _show_status(self):
        """Show AI tools status"""
        all_tools = self.service.get_installed_tools()

        status_table = Table(title="AI Tools Status", show_header=True, header_style="bold cyan")
        status_table.add_column("Tool", style="cyan", width=25)
        status_table.add_column("Status", style="white", width=20)

        for tool in all_tools:
            status = "[green]✓ Installed[/green]" if tool['installed'] else "[red]✗ Not installed[/red]"
            status_table.add_row(tool['name'], status)

        self.console.print("\n")
        self.console.print(status_table)
        self.console.input("\nPress Enter to continue...")

    def _show_about(self):
        """Show about information"""
        about = """
# About AI CLI Control

## What is it?

AI CLI Control gives AI tools **direct, autonomous control** over your LeadSauce system.
Unlike the conversational AI Assistant, this mode allows AI to execute operations
automatically to complete your requests.

## Use Cases

**Batch Operations:**
- "Create 10 test profiles for different companies"
- "Add reminders for all meetings next week"

**Data Management:**
- "Find all profiles without email and tag them as 'incomplete'"
- "Create a company for each unique domain in my profiles"

**Automation:**
- "Set up weekly reminders for my top 10 contacts"
- "Log interactions from this meeting notes file"

## Safety

- **Manual Mode:** You approve each command (recommended)
- **Auto-Execute Mode:** AI runs autonomously (use with caution)
- **Command Log:** Track all executed operations
- **Undo:** Database transactions allow rollback if needed

## How It Works

1. You give AI a high-level command
2. AI breaks it down into specific operations
3. AI generates JSON commands for each operation
4. System executes commands (with or without approval)
5. You see real-time results and feedback

This is the most powerful way to use AI with LeadSauce!
        """

        self.console.print(Panel(
            Markdown(about),
            title="[bold cyan]About AI CLI Control[/bold cyan]",
            border_style="cyan"
        ))
        self.console.input("\nPress Enter to continue...")
