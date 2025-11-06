"""Interactive AI Assistant for TUI

This module provides an interactive AI assistant interface for the LeadSauce TUI.
Users can ask questions, get coding help, and interact with AI tools directly
from the terminal interface.
"""

import subprocess
import threading
import queue
import time
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
**Commands:**
- Type your question or prompt and press Enter
- Type `/help` for all commands
- Type `/menu` to switch to another section
- Type `/context` to add files as context
- Type `/clear` to clear conversation history
- Type `/exit` or `/quit` to return to main menu

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

            self.show_welcome()
            context_files = []

            while True:
                try:
                    # Get user input
                    self.console.print()
                    user_input = Prompt.ask(
                        "[bold green]You[/bold green]",
                        console=self.console
                    ).strip()

                    if not user_input:
                        continue

                    # Handle special commands
                    if user_input.lower() in ['/exit', '/quit', '/q']:
                        self.console.print("[dim]Exiting Browser...[/dim]")
                        return None

                    elif user_input.lower() == '/help':
                        self._show_help()
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
                        continue

                    elif user_input.lower() == '/context':
                        context_files = self._add_context_files()
                        continue

                    elif user_input.lower() == '/history':
                        self._show_history()
                        continue

                    elif user_input.lower() == '/status':
                        self._show_status()
                        continue

                    # Send query to AI
                    self._send_query(user_input, context_files)

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

    def _send_query(self, prompt: str, context_files: Optional[List[str]] = None):
        """Send query to AI and display response

        Args:
            prompt: User's question/prompt
            context_files: Optional list of files for context
        """
        # Prepend system context on first message if system-aware mode
        full_prompt = prompt
        if self.system_aware and not self.system_context_sent:
            system_context = SystemContextProvider.get_contextualized_prompt()
            full_prompt = f"{system_context}\n\n---\n\nUser: {prompt}"
            self.system_context_sent = True

        # Show loading indicator
        try:
            self.console.print(f"\n[bold yellow]⚡ TIP: Press Ctrl+C anytime to cancel and switch menus[/bold yellow]\n")
            with self.console.status(
                f"[bold cyan]🤔 Asking {self.service.get_tool_info(self.tool)['name']}...[/bold cyan]",
                spinner="dots"
            ):
                response = self.service.query(
                    prompt=full_prompt,
                    tool=self.tool,
                    files=context_files,
                    working_dir=self.working_dir
                )

            # Store in history (store original prompt, not full with context)
            self.conversation_history.append({
                'role': 'user',
                'content': prompt,
                'timestamp': time.time()
            })
            self.conversation_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': time.time()
            })

            # Display response (outside status context)
            self.console.print()
            self.console.print(Panel(
                Markdown(response) if self._is_markdown(response) else Text(response),
                title=f"[bold cyan]🤖 {self.service.get_tool_info(self.tool)['name']}[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))

            # If system-aware mode, check for and execute commands (outside status context)
            if self.system_aware:
                self._execute_commands_from_response(response)

        except ToolNotInstalledError as e:
            self.console.print(Panel(
                f"[red]{str(e)}[/red]",
                title="Tool Not Installed",
                border_style="red"
            ))

        except ToolTimeoutError as e:
            self.console.print(Panel(
                f"[yellow]{str(e)}[/yellow]\n\n"
                "This usually happens with complex queries. Try:\n"
                "• Breaking your question into smaller parts\n"
                "• Being more specific\n"
                "• Reducing the amount of context",
                title="Timeout",
                border_style="yellow"
            ))

        except AICLIError as e:
            self.console.print(Panel(
                f"[red]{str(e)}[/red]",
                title="AI Error",
                border_style="red"
            ))

        except KeyboardInterrupt:
            self.console.print("\n[bold green]✓ Operation cancelled[/bold green]")
            self.console.print("[bold]You can now:[/bold]")
            self.console.print("  • Type another question")
            self.console.print("  • Type [cyan]/menu[/cyan] to switch to another section")
            self.console.print("  • Type [cyan]/exit[/cyan] to return to dashboard\n")
            raise  # Re-raise to be caught by outer handler

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
        help_table = Table(title="Browser Commands", show_header=True, header_style="bold cyan")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help message"),
            ("/context", "Add files as context for the AI"),
            ("/clear", "Clear conversation history"),
            ("/history", "Show conversation history"),
            ("/status", "Show AI tool status"),
            ("/menu", "Switch to another main menu"),
            ("/exit, /quit, /q", "Exit browser"),
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

        # Start session
        session = InteractiveAISession(tool=tool)
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
