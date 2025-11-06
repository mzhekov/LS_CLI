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


class InteractiveAISession:
    """Manage interactive AI assistant sessions in the TUI"""

    def __init__(self, tool: str = 'claude', working_dir: Optional[str] = None):
        """Initialize interactive AI session

        Args:
            tool: AI tool to use (claude, codex, aider)
            working_dir: Working directory for context
        """
        self.tool = tool
        self.working_dir = working_dir or str(Path.cwd())
        self.console = Console()
        self.service = AICLIService(default_tool=tool)
        self.conversation_history: List[Dict[str, str]] = []

    def show_welcome(self):
        """Display welcome message"""
        tool_info = self.service.get_tool_info(self.tool)

        welcome_text = f"""
# 🤖 AI Assistant - {tool_info['name']}

Welcome to the LeadSauce AI Assistant! You can:

• **Ask questions** about your code and data
• **Get help** with LeadSauce features
• **Generate code** snippets and scripts
• **Debug issues** and get suggestions
• **Analyze** your database schema

**Commands:**
- Type your question or prompt and press Enter
- Type `/help` for more commands
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

    def run(self):
        """Run the interactive AI session"""
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
                return

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
                        self.console.print("[dim]Exiting AI Assistant...[/dim]")
                        break

                    elif user_input.lower() == '/help':
                        self._show_help()
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
                    self.console.print("\n[dim]Use /exit to quit[/dim]")
                    continue

                except Exception as e:
                    self.console.print(f"[red]Error: {str(e)}[/red]")
                    continue

        except Exception as e:
            self.console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
            self.console.input("\nPress Enter to continue...")

    def _send_query(self, prompt: str, context_files: Optional[List[str]] = None):
        """Send query to AI and display response

        Args:
            prompt: User's question/prompt
            context_files: Optional list of files for context
        """
        # Show loading indicator
        with self.console.status(
            f"[bold cyan]Asking {self.service.get_tool_info(self.tool)['name']}...[/bold cyan]",
            spinner="dots"
        ):
            try:
                response = self.service.query(
                    prompt=prompt,
                    tool=self.tool,
                    files=context_files,
                    working_dir=self.working_dir
                )

                # Store in history
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

                # Display response
                self.console.print()
                self.console.print(Panel(
                    Markdown(response) if self._is_markdown(response) else Text(response),
                    title=f"[bold cyan]🤖 {self.service.get_tool_info(self.tool)['name']}[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2)
                ))

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

    def _show_help(self):
        """Display help information"""
        help_table = Table(title="AI Assistant Commands", show_header=True, header_style="bold cyan")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help message"),
            ("/context", "Add files as context for the AI"),
            ("/clear", "Clear conversation history"),
            ("/history", "Show conversation history"),
            ("/status", "Show AI tool status"),
            ("/exit, /quit, /q", "Exit AI assistant"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)

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

    def show(self):
        """Show AI assistant menu"""
        while True:
            # Get installed tools
            installed_tools = self.service.get_installed_tools()
            installed = [t for t in installed_tools if t['installed']]

            # Build menu choices
            choices = []

            if installed:
                choices.append("💬 Quick Ask (one question)")
                choices.append("🔄 Start Interactive Session")
                choices.append("📊 View AI Tools Status")
                choices.append("ℹ️  Help & Setup Guide")
            else:
                choices.append("⚠️  No AI Tools Installed - View Setup Guide")

            choices.append("← Back to Main Menu")

            # Show menu
            choice = questionary.select(
                "AI Assistant",
                choices=choices,
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                    ('question', 'fg:cyan bold'),
                ])
            ).ask()

            if choice == "← Back to Main Menu":
                break

            elif choice == "💬 Quick Ask (one question)":
                self._quick_ask(installed)

            elif choice == "🔄 Start Interactive Session":
                self._start_interactive_session(installed)

            elif choice == "📊 View AI Tools Status":
                self._show_status()

            elif choice in ["ℹ️  Help & Setup Guide", "⚠️  No AI Tools Installed - View Setup Guide"]:
                self._show_setup_guide()

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

    def _start_interactive_session(self, installed_tools: List[Dict]):
        """Start interactive AI session

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

            if not tool_choice:
                return

            tool = next(t['id'] for t in installed_tools if t['name'] in tool_choice)

        # Start session
        session = InteractiveAISession(tool=tool)
        session.run()

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
