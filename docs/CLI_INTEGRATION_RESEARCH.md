# CLI Integration Research: Claude Code, Codex CLI, and Similar Tools
## Research Document for LeadSauce CLI Integration

**Date:** November 6, 2025
**Purpose:** Research solutions for integrating AI CLI tools (Claude Code, Codex CLI, etc.) into LeadSauce CLI without API integration

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current Application Architecture](#current-application-architecture)
3. [AI CLI Tools Analysis](#ai-cli-tools-analysis)
4. [Integration Patterns Without API](#integration-patterns-without-api)
5. [Recommended Solutions](#recommended-solutions)
6. [Implementation Approaches](#implementation-approaches)
7. [Technical Considerations](#technical-considerations)
8. [Next Steps](#next-steps)

---

## Executive Summary

This document provides research findings on integrating AI-powered CLI tools (Claude Code, Codex CLI, GitHub Copilot CLI) into the LeadSauce CLI application **without direct API integration**. The key insight is that these tools can be invoked as **subprocess executables** from within the LeadSauce CLI, leveraging their existing CLI interfaces.

### Key Findings:
- **Claude Code, Codex CLI, and similar tools are standalone CLI applications** that can be invoked via subprocess
- **No API integration required** - they work through stdin/stdout communication
- **Multiple integration patterns available**: subprocess wrapper, PTY integration, and Model Context Protocol (MCP)
- **LeadSauce CLI is well-positioned** for this integration due to its Click-based architecture and Rich terminal UI

---

## Current Application Architecture

### LeadSauce CLI Overview

**Type:** Professional Network Management Command-Line Interface (CLI)
**Language:** Python 3.9+
**Primary Framework:** Click (8.1.0+)
**Architecture:** Modular CLI with interactive TUI mode

### Core Components

```
leadsauce/
├── cli.py                      # Main CLI entry (Click-based)
├── commands/                   # Command groups (profile, company, export, import, auth)
├── models/                     # SQLAlchemy ORM models
├── utils/                      # Utilities including:
│   ├── interactive.py          # Rich TUI system (205KB - extensive)
│   ├── dashboard.py            # Terminal dashboard
│   ├── formatters.py           # Output formatting
│   └── db.py                   # Database management
├── services/                   # Business logic (placeholder)
└── api/                        # API integration (placeholder)
```

### Key Characteristics
- ✅ **Structured CLI** using Click framework
- ✅ **Rich Interactive TUI** with keyboard navigation
- ✅ **Database persistence** (SQLAlchemy - SQLite/PostgreSQL/MySQL)
- ✅ **Modular command structure** (easy to extend)
- ✅ **Professional terminal UI** using Rich library
- ✅ **Configuration management** via YAML
- ✅ **Multiple output formats** (table, JSON, CSV, text)

### Integration Opportunities

The existing `api/` and `services/` directories are currently placeholders, making them **ideal locations** for AI CLI integration services.

---

## AI CLI Tools Analysis

### 1. Claude Code (Anthropic)

**Architecture:**
- **Tech Stack:** TypeScript, React, Ink, Yoga, Bun
- **Philosophy:** Low-level, unopinionated, close to raw model access
- **Execution:** Runs locally (no virtualization)
- **Installation:** `npm install -g @anthropic-ai/claude-code`

**How It Works:**
- Ingests and indexes codebases on first run
- Develops internal representation of architecture
- Supports **MCP (Model Context Protocol)** as both server and client
- Uses `.claude/commands/` folder for custom prompt templates
- Uses `CLAUDE.md` files for project context

**Key Features:**
- Custom slash commands via Markdown templates
- Project context management
- Direct terminal integration
- Conversational interface: `claude "query"`
- Resume last conversation: `claude -c`

**Requirements:**
- Paid Claude.ai subscription
- Node.js/npm installed

---

### 2. OpenAI Codex CLI

**Architecture:**
- **Language:** Open-source CLI tool
- **Execution:** Runs locally, interactive terminal UI
- **Integration:** Can create PRs in GitHub, run browser for inspections

**How It Works:**
- Interactive terminal UI for code operations
- Multiple approval modes (default vs read-only)
- Can read codebase, make edits, run commands
- Source code stays local unless explicitly shared
- Network access requires approval

**Key Features:**
- `/approvals` command to switch modes
- Review changes as diffs before committing
- Create PRs directly from CLI
- GitHub Actions integration for CI/CD
- Screenshot sharing in PRs

**Installation:**
- `codex` command
- Sign in with ChatGPT (Plus/Pro/Team/Edu/Enterprise)
- Open-source: `github.com/openai/codex`

---

### 3. Other Notable AI CLI Tools (2025)

#### GitHub Copilot CLI
- Released September 25, 2025
- Agentic coding assistant in terminal
- Deep integration with GitHub workflows

#### Gemini CLI (Google)
- Announced June 25, 2025
- Uses Gemini 2.5 Pro model
- **Open-source (Apache-2.0)**
- Supports MCP for extensibility

#### Warp Terminal & Wave Terminal
- Fully integrated AI throughout interface
- Support for multiple models (OpenAI, Claude, Ollama)
- Can operate offline with local LLMs

---

## Integration Patterns Without API

### Pattern 1: Subprocess Wrapper (Recommended for LeadSauce)

**Concept:** Invoke AI CLI tools as subprocess executables from Python

**Technology:**
- Python `subprocess` module
- `subprocess.run()` for one-off commands
- `subprocess.Popen()` for interactive sessions
- `communicate()` method for stdin/stdout interaction

**Example Architecture:**
```python
import subprocess

class ClaudeCodeWrapper:
    def __init__(self):
        self.command = "claude"

    def query(self, prompt: str, context_files: list = None) -> str:
        """Send a query to Claude Code CLI"""
        cmd = [self.command, prompt]
        if context_files:
            for file in context_files:
                cmd.extend(["--file", file])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout

    def interactive_session(self):
        """Start interactive Claude Code session"""
        subprocess.run([self.command, "-c"])
```

**Advantages:**
- ✅ No API keys or authentication needed (uses CLI's existing auth)
- ✅ Simple implementation
- ✅ Works with any CLI tool
- ✅ Can capture output for display in LeadSauce TUI
- ✅ Users maintain control over AI tool subscriptions

**Use Cases in LeadSauce:**
- Generate code snippets for custom queries
- Analyze database schema
- Suggest profile data enrichment strategies
- Auto-generate import/export scripts
- Code review for user-contributed extensions

---

### Pattern 2: PTY (Pseudo-Terminal) Integration

**Concept:** Use pseudo-terminal to interact with AI CLI tools that require interactive terminal behavior

**Technology:**
- `ptyprocess` library (Python)
- Python's built-in `pty` module
- Handles programs that behave differently in pipes vs terminals

**Why PTY Instead of Subprocess:**
Many CLI tools detect if stdin/stdout is a pipe vs terminal and change behavior:
- Password prompts
- Colored output
- Progress bars
- Curses-style interfaces

**Example Architecture:**
```python
import ptyprocess

class InteractiveClaudeCLI:
    def __init__(self):
        self.process = None

    def start(self):
        """Start Claude Code in a pseudo-terminal"""
        self.process = ptyprocess.PtyProcess.spawn(['claude', '-c'])

    def send_command(self, command: str):
        """Send command to running Claude session"""
        self.process.write(command.encode() + b'\n')

    def read_output(self, timeout=5):
        """Read output from Claude"""
        return self.process.read().decode()

    def close(self):
        """Close the PTY session"""
        if self.process:
            self.process.close()
```

**Advantages:**
- ✅ Preserves interactive behavior of CLI tools
- ✅ Handles color codes and formatted output
- ✅ Can embed interactive sessions within LeadSauce TUI
- ✅ Real-time streaming of responses

**Libraries:**
- `ptyprocess`: https://pypi.org/project/ptyprocess/
- `pexpect`: Higher-level wrapper around ptyprocess

---

### Pattern 3: Model Context Protocol (MCP) Integration

**Concept:** Use MCP to standardize communication between LeadSauce and AI CLI tools

**Technology:**
- MCP Python SDK: `pip install mcp[cli]`
- FastMCP: `pip install fastmcp` (simpler, Pythonic alternative)
- Standard transports: stdio, SSE, HTTP

**MCP Components:**
- **Resources:** Expose data (like GET endpoints)
- **Tools:** Provide functionality (like POST endpoints)
- **Prompts:** Define reusable templates for LLM interactions

**Example Architecture:**

```python
# LeadSauce as MCP Server (exposes data to AI tools)
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("leadsauce-mcp")

@app.list_resources()
async def list_resources():
    """Expose LeadSauce profiles as resources"""
    return [
        {
            "uri": "leadsauce://profiles",
            "name": "All Profiles",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str):
    """Provide profile data to AI tools"""
    if uri == "leadsauce://profiles":
        # Query profiles from database
        profiles = get_all_profiles()
        return json.dumps(profiles)

# Run MCP server
async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1])
```

```python
# LeadSauce as MCP Client (consumes AI tool capabilities)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_claude_via_mcp():
    """Connect to Claude Code via MCP"""
    server_params = StdioServerParameters(
        command="claude",
        args=["--mcp"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools from Claude
            tools = await session.list_tools()

            # Call a tool
            result = await session.call_tool(
                "analyze_code",
                {"file": "leadsauce/models/profile.py"}
            )
            return result
```

**Advantages:**
- ✅ Standardized protocol (works with Claude Code, Gemini CLI, etc.)
- ✅ Both client and server capabilities
- ✅ Async/await support for performance
- ✅ Can expose LeadSauce data to AI tools
- ✅ Can consume AI tool capabilities

**Disadvantages:**
- ⚠️ More complex than subprocess approach
- ⚠️ Requires AI CLI tools to support MCP
- ⚠️ Additional dependency management

---

### Pattern 4: Shell Command Delegation

**Concept:** Create LeadSauce commands that delegate to AI CLI tools directly

**Example:**
```python
# In leadsauce/commands/ai.py
import click
import subprocess

@click.group()
def ai():
    """AI-powered assistance commands"""
    pass

@ai.command()
@click.argument('prompt')
def claude(prompt):
    """Ask Claude Code a question"""
    subprocess.run(['claude', prompt])

@ai.command()
@click.argument('prompt')
def codex(prompt):
    """Ask Codex CLI a question"""
    subprocess.run(['codex', prompt])
```

**Usage:**
```bash
leadsauce ai claude "Help me optimize my profile queries"
leadsauce ai codex "Generate a CSV export script"
```

**Advantages:**
- ✅ Extremely simple implementation
- ✅ Unified interface (users don't need to switch between tools)
- ✅ Can add pre/post-processing logic
- ✅ Maintain LeadSauce context

---

## Recommended Solutions

### For LeadSauce CLI: Three-Tier Approach

#### Tier 1: Simple Integration (MVP - Recommended Start)
**Implementation:** Subprocess wrapper with basic commands

```python
# leadsauce/services/ai_cli.py
import subprocess
from typing import Optional

class AICLIService:
    """Service for interacting with AI CLI tools"""

    @staticmethod
    def is_installed(tool: str) -> bool:
        """Check if AI CLI tool is installed"""
        try:
            subprocess.run([tool, '--version'],
                          capture_output=True,
                          timeout=5)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def claude_query(prompt: str, files: list = None) -> str:
        """Query Claude Code CLI"""
        if not AICLIService.is_installed('claude'):
            return "Error: Claude Code CLI not installed"

        cmd = ['claude', prompt]
        result = subprocess.run(cmd,
                               capture_output=True,
                               text=True,
                               timeout=300)
        return result.stdout

    @staticmethod
    def codex_query(prompt: str) -> str:
        """Query Codex CLI"""
        if not AICLIService.is_installed('codex'):
            return "Error: Codex CLI not installed"

        cmd = ['codex', prompt]
        result = subprocess.run(cmd,
                               capture_output=True,
                               text=True,
                               timeout=300)
        return result.stdout
```

```python
# leadsauce/commands/ai.py
import click
from leadsauce.services.ai_cli import AICLIService
from leadsauce.utils.formatters import print_success, print_error

@click.group()
def ai():
    """AI-powered coding assistance"""
    pass

@ai.command()
@click.argument('prompt')
@click.option('--tool', type=click.Choice(['claude', 'codex']),
              default='claude')
def ask(prompt, tool):
    """Ask an AI coding assistant"""
    service = AICLIService()

    if tool == 'claude':
        response = service.claude_query(prompt)
    else:
        response = service.codex_query(prompt)

    print_success(response)

@ai.command()
def status():
    """Check which AI CLI tools are installed"""
    tools = ['claude', 'codex', 'gh']
    for tool in tools:
        installed = AICLIService.is_installed(tool)
        status = "✓ Installed" if installed else "✗ Not installed"
        click.echo(f"{tool}: {status}")
```

**Timeline:** 1-2 days
**Complexity:** Low
**Value:** High (immediate AI assistance access)

---

#### Tier 2: Interactive Integration (Enhanced)
**Implementation:** PTY-based interactive sessions within LeadSauce TUI

```python
# leadsauce/utils/ai_interactive.py
import ptyprocess
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

class InteractiveAISession:
    """Manage interactive AI CLI sessions"""

    def __init__(self, tool: str = 'claude'):
        self.tool = tool
        self.process = None
        self.console = Console()

    def start(self):
        """Start interactive session"""
        try:
            self.process = ptyprocess.PtyProcess.spawn([self.tool, '-c'])
            return True
        except Exception as e:
            self.console.print(f"[red]Failed to start {self.tool}: {e}[/red]")
            return False

    def run_conversation(self):
        """Run interactive conversation loop"""
        with Live(Panel("Starting AI session..."), console=self.console) as live:
            while True:
                # Get user input
                user_input = self.console.input("\n[bold cyan]You:[/bold cyan] ")

                if user_input.lower() in ['exit', 'quit', '/quit']:
                    break

                # Send to AI tool
                self.process.write(user_input.encode() + b'\n')

                # Read response (with timeout)
                response = self._read_response(timeout=30)

                # Display in Rich panel
                live.update(Panel(response, title=f"{self.tool.title()} Response"))

    def _read_response(self, timeout: int = 30) -> str:
        """Read response from PTY with timeout"""
        import select
        output = []

        while True:
            if select.select([self.process.fd], [], [], timeout)[0]:
                try:
                    chunk = self.process.read()
                    output.append(chunk.decode())
                except EOFError:
                    break
            else:
                break

        return ''.join(output)

    def close(self):
        """Close the session"""
        if self.process:
            self.process.close()
```

**Add to TUI menu:**
```python
# In leadsauce/utils/interactive.py - add to main menu
def show_ai_assistant_menu(self):
    """Interactive AI Assistant menu"""
    choices = [
        "Start Claude Code Session",
        "Start Codex Session",
        "Quick Ask Claude",
        "Quick Ask Codex",
        "View AI Tools Status",
        "← Back to Main Menu"
    ]

    choice = questionary.select(
        "AI Assistant",
        choices=choices
    ).ask()

    if choice == "Start Claude Code Session":
        session = InteractiveAISession('claude')
        if session.start():
            session.run_conversation()
        session.close()
```

**Timeline:** 3-5 days
**Complexity:** Medium
**Value:** High (seamless AI integration within LeadSauce UI)

---

#### Tier 3: MCP Integration (Advanced)
**Implementation:** Full MCP server/client for bi-directional communication

**LeadSauce as MCP Server** (AI tools can query LeadSauce data):
```python
# leadsauce/services/mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from leadsauce.models.profile import Profile
from leadsauce.utils.db import get_session
import json

app = Server("leadsauce")

@app.list_resources()
async def list_resources():
    """Expose LeadSauce data sources"""
    return [
        {"uri": "leadsauce://profiles", "name": "All Profiles"},
        {"uri": "leadsauce://companies", "name": "All Companies"},
        {"uri": "leadsauce://interactions", "name": "All Interactions"},
        {"uri": "leadsauce://schema", "name": "Database Schema"}
    ]

@app.read_resource()
async def read_resource(uri: str):
    """Provide data to AI tools"""
    session = get_session()

    if uri == "leadsauce://profiles":
        profiles = session.query(Profile).all()
        data = [p.to_dict() for p in profiles]
        return json.dumps(data, indent=2)

    elif uri == "leadsauce://schema":
        # Return database schema for AI understanding
        schema = {
            "Profile": Profile.__table__.columns.keys(),
            # ... other models
        }
        return json.dumps(schema, indent=2)

@app.list_tools()
async def list_tools():
    """Expose LeadSauce operations as tools"""
    return [
        {
            "name": "create_profile",
            "description": "Create a new profile in LeadSauce",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "company": {"type": "string"}
                },
                "required": ["name"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute LeadSauce operations from AI tools"""
    session = get_session()

    if name == "create_profile":
        profile = Profile(**arguments)
        session.add(profile)
        session.commit()
        return f"Created profile: {profile.name}"

# CLI command to start MCP server
@click.command()
def mcp_server():
    """Start LeadSauce MCP server"""
    import asyncio

    async def run():
        async with stdio_server() as streams:
            await app.run(streams[0], streams[1])

    asyncio.run(run())
```

**Configuration in Claude Code:**
```json
// ~/.config/claude/mcp.json
{
  "mcpServers": {
    "leadsauce": {
      "command": "leadsauce",
      "args": ["mcp-server"]
    }
  }
}
```

**Usage:**
```bash
# Start Claude Code with LeadSauce context
claude "Analyze my LeadSauce profiles and suggest improvements"

# Claude Code can now:
# - Read profiles, companies, interactions
# - Create new profiles
# - Understand database schema
# - Generate LeadSauce-specific code
```

**Timeline:** 1-2 weeks
**Complexity:** High
**Value:** Very High (full bi-directional integration)

---

## Implementation Approaches

### Approach A: Command Group (Fastest - Recommended First Step)

**What:** Add `ai` command group to LeadSauce CLI

```bash
leadsauce ai ask "How do I optimize my database queries?"
leadsauce ai claude "Generate a CSV export script"
leadsauce ai codex "Explain this code: <file>"
leadsauce ai status
```

**Implementation Steps:**
1. Create `leadsauce/services/ai_cli.py` with wrapper class
2. Create `leadsauce/commands/ai.py` with Click commands
3. Register command group in `leadsauce/cli.py`
4. Add status checking for installed tools
5. Document in README

**Pros:**
- Quick to implement (2-3 hours)
- Non-invasive to existing code
- Easy to test and iterate
- Users can opt-in/out easily

---

### Approach B: TUI Integration (Best UX)

**What:** Add AI assistant menu to existing interactive TUI

**Location in TUI:**
- Add "AI Assistant" to top navigation bar (keyboard shortcut: 8)
- Or: Add as submenu under "Workshop"

**Features:**
- Start interactive AI session
- Quick question/answer
- Code generation with preview
- Tool status checker

**Implementation Steps:**
1. Implement Approach A first (foundation)
2. Add `InteractiveAISession` class to `leadsauce/utils/ai_interactive.py`
3. Add menu item to `leadsauce/utils/interactive.py`
4. Style with Rich library (match existing UI)
5. Add keyboard shortcuts

**Pros:**
- Seamless user experience
- Stays within LeadSauce workflow
- Can show AI responses in Rich panels
- Better for non-technical users

---

### Approach C: MCP Server (Most Powerful)

**What:** Make LeadSauce data/operations accessible to AI tools via MCP

**Capabilities:**
- AI tools can query LeadSauce database
- AI tools can understand LeadSauce schema
- AI tools can create/update profiles
- AI tools can generate context-aware code

**Implementation Steps:**
1. Add `mcp` dependency to requirements.txt
2. Create `leadsauce/services/mcp_server.py`
3. Expose resources (profiles, companies, etc.)
4. Expose tools (CRUD operations)
5. Add `leadsauce mcp-server` command
6. Document MCP configuration for Claude Code/Gemini CLI

**Pros:**
- Standard protocol (future-proof)
- Works with multiple AI tools
- Enables sophisticated AI assistance
- Can replace custom API integrations

**Cons:**
- Higher complexity
- Requires MCP-compatible AI tools
- More maintenance

---

## Technical Considerations

### 1. Dependencies

**Minimum (Approach A):**
```txt
# No additional dependencies needed!
# Uses Python's built-in subprocess module
```

**Enhanced (Approach B):**
```txt
ptyprocess>=0.7.0  # For interactive PTY sessions
pexpect>=4.8.0     # Higher-level PTY wrapper (optional)
```

**Advanced (Approach C):**
```txt
mcp[cli]>=1.0.0    # Model Context Protocol SDK
# OR
fastmcp>=0.1.0     # Simpler MCP alternative
```

### 2. Prerequisites for Users

**Required:**
- AI CLI tool installed (e.g., `npm install -g @anthropic-ai/claude-code`)
- Active subscription to AI service (Claude.ai, ChatGPT Plus, etc.)

**Optional:**
- MCP configuration (for Approach C)

### 3. Error Handling

```python
class AICLIError(Exception):
    """Base exception for AI CLI integration"""
    pass

class ToolNotInstalledError(AICLIError):
    """Raised when AI CLI tool is not installed"""
    pass

class ToolTimeoutError(AICLIError):
    """Raised when AI CLI tool times out"""
    pass

# Usage
try:
    response = service.claude_query(prompt)
except ToolNotInstalledError:
    print_error("Claude Code CLI is not installed. Run: npm install -g @anthropic-ai/claude-code")
except ToolTimeoutError:
    print_error("Claude Code timed out. Try a simpler query.")
except AICLIError as e:
    print_error(f"AI CLI error: {e}")
```

### 4. Configuration

**Add to `~/.leadsauce/config.yaml`:**
```yaml
ai:
  enabled: true
  default_tool: claude  # claude, codex, gemini
  timeout: 300  # seconds
  tools:
    claude:
      command: claude
      enabled: true
    codex:
      command: codex
      enabled: true
    gemini:
      command: gemini
      enabled: false
  mcp:
    enabled: false
    port: 3000
```

### 5. Security Considerations

**Data Privacy:**
- ⚠️ AI CLI tools may send data to external services
- ✅ Data is only sent when user explicitly invokes AI commands
- ✅ Users control which AI tools they install/use
- ✅ Subprocess isolation (no direct API key exposure)

**Recommendations:**
- Add warning on first AI command use
- Allow users to disable AI features in config
- Provide clear documentation on data handling
- Consider adding `--no-ai` flag to disable globally

### 6. Cross-Platform Compatibility

**Windows:**
- ⚠️ PTY support limited (use `winpty` or Windows Terminal)
- ✅ Subprocess approach works fine
- ✅ MCP approach works fine

**macOS/Linux:**
- ✅ Full PTY support
- ✅ All approaches work

**Recommendation:** Start with subprocess approach (works everywhere), add PTY later for Unix systems

---

## Next Steps

### Phase 1: MVP (Week 1)
**Goal:** Basic AI CLI integration

**Tasks:**
1. ✅ Research complete (this document)
2. Create `leadsauce/services/ai_cli.py`
3. Create `leadsauce/commands/ai.py`
4. Add `ai` command group to CLI
5. Implement basic commands:
   - `leadsauce ai ask <prompt>`
   - `leadsauce ai status`
   - `leadsauce ai config`
6. Add to `~/.leadsauce/config.yaml`
7. Write tests
8. Update README.md

**Deliverable:** Users can run `leadsauce ai ask "question"` and get responses

---

### Phase 2: Enhanced Integration (Week 2-3)
**Goal:** Seamless TUI integration

**Tasks:**
1. Implement `InteractiveAISession` class
2. Add AI Assistant menu to TUI
3. Add keyboard shortcuts (8 key for AI menu)
4. Implement PTY-based interactive sessions
5. Add Rich-styled output panels
6. Create quick-ask dialog in TUI
7. Add context-aware prompts (auto-include current view data)

**Deliverable:** Users can access AI from within TUI without leaving LeadSauce

---

### Phase 3: MCP Integration (Week 4-6)
**Goal:** Bi-directional AI integration

**Tasks:**
1. Add MCP dependencies
2. Implement MCP server exposing LeadSauce data
3. Expose resources (profiles, companies, interactions)
4. Expose tools (CRUD operations)
5. Add `leadsauce mcp-server` command
6. Create MCP configuration guide
7. Test with Claude Code, Gemini CLI
8. Document advanced workflows

**Deliverable:** AI tools can natively query/modify LeadSauce data

---

### Testing Strategy

**Unit Tests:**
```python
# tests/test_services/test_ai_cli.py
def test_tool_detection():
    assert AICLIService.is_installed('python') == True
    assert AICLIService.is_installed('fake_tool_xyz') == False

def test_claude_query_not_installed(monkeypatch):
    monkeypatch.setattr(AICLIService, 'is_installed', lambda x: False)
    result = AICLIService.claude_query("test")
    assert "not installed" in result

# Mock subprocess for testing
@patch('subprocess.run')
def test_claude_query_success(mock_run):
    mock_run.return_value = MagicMock(stdout="AI response")
    result = AICLIService.claude_query("test")
    assert result == "AI response"
```

**Integration Tests:**
```python
# tests/test_commands/test_ai.py
def test_ai_status_command(cli_runner):
    result = cli_runner.invoke(ai, ['status'])
    assert result.exit_code == 0
    assert 'claude' in result.output

def test_ai_ask_command(cli_runner):
    result = cli_runner.invoke(ai, ['ask', 'What is Python?'])
    assert result.exit_code == 0
```

---

## Conclusion

Integrating AI CLI tools into LeadSauce CLI **without API integration** is not only feasible but recommended. The subprocess approach provides a clean, simple integration that:

✅ **Requires no API keys** - uses CLI tools' existing authentication
✅ **Maintains separation** - LeadSauce doesn't need AI service accounts
✅ **Offers flexibility** - supports multiple AI tools (Claude, Codex, Gemini)
✅ **Scales well** - can evolve from simple commands to MCP integration
✅ **Respects user choice** - users control which AI tools they install/use

### Recommended Path:
1. **Start with Approach A** (command group) - 2-3 hours of work, immediate value
2. **Add Approach B** (TUI integration) - Better UX, 3-5 days
3. **Consider Approach C** (MCP) - Long-term investment, 1-2 weeks

### Success Metrics:
- Users can invoke AI from within LeadSauce CLI
- No additional authentication/API keys required
- Seamless experience without leaving terminal
- Works with multiple AI CLI tools

---

## References

### Documentation
- Claude Code: https://docs.claude.com/claude-code
- Codex CLI: https://github.com/openai/codex
- MCP: https://modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- ptyprocess: https://ptyprocess.readthedocs.io/

### Libraries
- subprocess: https://docs.python.org/3/library/subprocess.html
- ptyprocess: https://pypi.org/project/ptyprocess/
- mcp: https://pypi.org/project/mcp/
- fastmcp: https://github.com/jlowin/fastmcp

### Articles
- "How Claude Code is Built": https://newsletter.pragmaticengineer.com/p/how-claude-code-is-built
- "Compare Top 5 Agentic CLI Tools": https://getstream.io/blog/agentic-cli-tools/

---

**Document Version:** 1.0
**Last Updated:** November 6, 2025
**Author:** Research conducted via Claude Code
