# AI Assistant Integration Guide

## Overview

LeadSauce CLI now includes an integrated AI Assistant that brings AI-powered coding help directly into your terminal workflow. Ask questions, get coding help, and interact with AI tools like Claude Code, Codex CLI, and Aider without leaving the TUI.

## Features

✨ **Interactive Sessions** - Have back-and-forth conversations with AI tools
🎯 **Quick Ask Mode** - Get quick answers to single questions
📁 **Context Support** - Add files as context for better AI understanding
🔧 **Multi-Tool Support** - Works with Claude Code, Codex CLI, and Aider
📊 **Status Dashboard** - See which AI tools are installed
💬 **Beautiful TUI** - Seamless integration with LeadSauce's Rich terminal UI

## Accessing the AI Assistant

### From the TUI Main Menu

1. Launch LeadSauce TUI:
   ```bash
   leadsauce tui
   ```

2. Press `0` (zero) or navigate to **AI Assistant** 🤖

3. Choose your mode:
   - **💬 Quick Ask** - Single question mode
   - **🔄 Interactive Session** - Full conversation mode
   - **📊 View Status** - Check installed tools
   - **ℹ️ Help & Setup** - Installation guide

### Keyboard Shortcuts

From any TUI screen, press:
- `0` - Open AI Assistant menu

## Supported AI Tools

### 1. Claude Code (Anthropic)

**Installation:**
```bash
npm install -g @anthropic-ai/claude-code
```

**Requirements:**
- Node.js installed
- Paid Claude.ai subscription

**Best For:**
- Python development
- Code understanding
- LeadSauce-specific queries

### 2. Codex CLI (OpenAI)

**Installation:**
Follow instructions at: https://github.com/openai/codex

**Requirements:**
- ChatGPT Plus, Pro, Team, or Enterprise subscription

**Best For:**
- GitHub integration
- PR creation
- Multiple language support

### 3. Aider (Open Source)

**Installation:**
```bash
pip install aider-chat
```

**Requirements:**
- OpenAI API key (set `OPENAI_API_KEY` environment variable)
- Or use local models with `--model` flag

**Best For:**
- Open source alternative
- Git integration
- Custom model support

## Usage Examples

### Quick Ask Mode

1. Select **💬 Quick Ask**
2. Choose your AI tool (if multiple installed)
3. Type your question
4. Get instant answer

Example questions:
- "How do I optimize database queries in LeadSauce?"
- "Explain the Profile model structure"
- "Generate a CSV export script for all profiles"
- "What's the best way to add a new field to Company?"

### Interactive Session Mode

1. Select **🔄 Start Interactive Session**
2. Choose your AI tool
3. Start conversation with multi-turn dialogue

**Available Commands:**
- `/help` - Show command list
- `/context` - Add files as context
- `/clear` - Clear conversation history
- `/history` - View conversation history
- `/status` - Show tool status
- `/exit` or `/quit` - Exit session

**Example Session:**
```
You: How does the Profile model work?
AI: The Profile model in LeadSauce represents...

You: Can you show me how to query profiles by company?
AI: Here's an example query...

You: /context
File 1: leadsauce/models/profile.py
File 2:

You: Now generate code to export all profiles from company X
AI: Based on the Profile model you provided...
```

### Adding Context Files

Context files help AI understand your specific code:

1. In interactive mode, type `/context`
2. Enter file paths (relative or absolute)
3. Press Enter on empty line to finish
4. Ask questions with full context

**Example:**
```
/context
File 1: leadsauce/models/profile.py
File 2: leadsauce/commands/export.py
File 3:

You: How do I add a new export format based on these files?
```

## Configuration

AI Assistant settings are stored in `~/.leadsauce/config.yaml`:

```yaml
ai:
  enabled: true
  default_tool: claude  # claude, codex, or aider
  timeout: 300  # seconds
  tools:
    claude:
      command: claude
      enabled: true
    codex:
      command: codex
      enabled: true
    aider:
      command: aider
      enabled: true
```

### Changing Default Tool

Edit your config file:
```bash
vim ~/.leadsauce/config.yaml
```

Change `default_tool`:
```yaml
ai:
  default_tool: codex  # Change to your preferred tool
```

### Adjusting Timeout

For complex queries that take longer:
```yaml
ai:
  timeout: 600  # Increase to 10 minutes
```

### Disabling Specific Tools

To hide a tool from the menu:
```yaml
ai:
  tools:
    aider:
      enabled: false  # Won't appear in tool selection
```

## Common Use Cases

### 1. Learning LeadSauce Codebase

**Question:**
```
Explain how the interaction tracking system works
```

**Question:**
```
What's the relationship between Profile and Company models?
```

### 2. Generating Code

**Question:**
```
Generate a script to bulk import profiles from LinkedIn CSV
```

**Question:**
```
Create a custom export function that includes relationship data
```

### 3. Debugging Issues

**Question:**
```
Why might my profile queries be slow?
```

**With context:**
```
/context
File 1: leadsauce/commands/profile.py

You: This query is slow, how can I optimize it?
```

### 4. Adding Features

**Question:**
```
How would I add a "last contacted" field to profiles?
```

**Question:**
```
Walk me through adding a new interaction type
```

### 5. Database Operations

**Question:**
```
How do I safely migrate the database schema?
```

**Question:**
```
Generate an Alembic migration for adding a field
```

## Tips for Best Results

### Be Specific
❌ "How does this work?"
✅ "How does the Profile.to_dict() method serialize data?"

### Provide Context
❌ "Fix this query"
✅ "This query in profile.py:145 is slow. Here's the code: [paste code]. How can I optimize it?"

### Use Interactive Mode for Complex Tasks
- Quick Ask: Simple, single questions
- Interactive: Multi-step problems, refinement, back-and-forth

### Add Files as Context
For questions about specific code:
1. Use `/context` command
2. Add relevant files
3. AI will have full code visibility

### Start Broad, Then Narrow
```
You: What are the main components of LeadSauce?
AI: [explains architecture]

You: Tell me more about the Profile model
AI: [detailed explanation]

You: How do I add validation to email field?
AI: [specific solution]
```

## Troubleshooting

### "Tool Not Installed" Error

**Problem:** Selected AI tool is not installed

**Solution:**
1. Check status: Select **📊 View AI Tools Status**
2. Install missing tool (see installation instructions above)
3. Verify installation: Run tool command directly in terminal

### Timeout Errors

**Problem:** Query times out after 5 minutes

**Solutions:**
- Break complex questions into smaller parts
- Reduce context files
- Increase timeout in config:
  ```yaml
  ai:
    timeout: 600  # 10 minutes
  ```

### "Command Not Found" Errors

**Problem:** AI CLI command not in PATH

**Solution:**
- Ensure tool is installed globally
- Check PATH includes installation directory
- For Claude Code: `npm install -g @anthropic-ai/claude-code`
- For Aider: `pip install aider-chat`

### No AI Tools Installed

**Problem:** Menu shows "No AI Tools Installed"

**Solution:**
1. Select **ℹ️ Help & Setup Guide**
2. Follow installation instructions for at least one tool
3. Restart LeadSauce TUI
4. Status should now show ✓ Installed

### AI Responses Are Not Helpful

**Solutions:**
- Add more context with `/context` command
- Be more specific in your question
- Provide code snippets or file references
- Use interactive mode for refinement

## Privacy & Security

### What Data Is Sent?

When you use AI Assistant:
- Your question/prompt is sent to the AI tool
- Any files you add with `/context` are sent
- Conversation history (in interactive mode) is sent

### Data Privacy

- **Local Execution:** AI CLI tools run locally on your machine
- **No Automatic Sharing:** Data is only sent when you explicitly ask questions
- **User Control:** You control which tools you install and use
- **Subscription Required:** Most tools require paid subscriptions from their providers

### Best Practices

1. **Don't share sensitive data** in prompts (API keys, passwords, etc.)
2. **Review files before adding as context** - make sure they don't contain secrets
3. **Use local models** for maximum privacy (Aider supports local LLMs)
4. **Check tool privacy policies** - understand how each provider handles data

## Advanced Features

### Custom Tool Commands

Edit config to use custom commands:

```yaml
ai:
  tools:
    custom_llm:
      command: /path/to/my-ai-tool
      enabled: true
```

### Working Directory Context

AI tools automatically use your current working directory as context. They can:
- Read project structure
- Understand file organization
- Generate code that matches your patterns

### Integration with LeadSauce Data

Ask questions about your actual data:

```
How many profiles do I have in the database?
```

```
Generate a report of my top 10 companies by profile count
```

*Note: AI tools can't directly access your database, but can help you write queries.*

## Future Enhancements

Planned features for AI Assistant:

- [ ] Direct database query execution
- [ ] Automated code generation with file creation
- [ ] MCP (Model Context Protocol) server for deeper integration
- [ ] Custom slash commands for common tasks
- [ ] AI-powered profile enrichment
- [ ] Automated relationship suggestions
- [ ] Smart import/export template generation

## Getting Help

### In-App Help
- Press `0` to open AI Assistant
- Select **ℹ️ Help & Setup Guide**
- Use `/help` in interactive sessions

### Documentation
- Main docs: `docs/CLI_INTEGRATION_RESEARCH.md`
- This guide: `docs/AI_ASSISTANT_GUIDE.md`

### Common Questions

**Q: Do I need all three AI tools installed?**
A: No, install whichever you prefer. One is enough.

**Q: Which tool is best?**
A:
- **Claude Code**: Best for Python, great code understanding
- **Codex**: Best GitHub integration, good for multiple languages
- **Aider**: Open source, local model support, budget-friendly

**Q: Does this cost extra?**
A: You need a subscription to the AI provider (Claude.ai, ChatGPT, or OpenAI API). LeadSauce itself doesn't charge for this feature.

**Q: Can I use local/offline models?**
A: Yes! Use Aider with local models:
```bash
aider --model ollama/codellama
```

**Q: Is my code/data private?**
A: Prompts and context are sent to AI providers. Review their privacy policies. Use local models for maximum privacy.

## Examples Gallery

### Generate Export Script
```
You: Generate a Python script to export all profiles to JSON with relationships included

AI: Here's a script that exports profiles with relationships:
[provides code]

You: Can you add error handling and progress bar?

AI: Sure, here's the updated version:
[provides improved code]
```

### Understand Database Schema
```
You: /context
File 1: leadsauce/models/profile.py
File 2: leadsauce/models/company.py
File 3: leadsauce/models/relationship.py

You: Create a diagram showing relationships between these models

AI: Based on your models, here's the relationship structure:
[provides explanation and ASCII diagram]
```

### Debug Performance Issue
```
You: /context
File 1: leadsauce/commands/profile.py

You: The list_profiles function at line 145 is very slow with 1000+ profiles. How can I optimize it?

AI: I see the issue. You're loading all relationships eagerly...
[provides analysis and solution]
```

### Add New Feature
```
You: I want to add a "lead score" field to profiles that calculates based on interaction frequency and recency. Walk me through implementation.

AI: Great idea! Here's a step-by-step approach:
1. Database: Add field to Profile model
2. Migration: Create Alembic migration
3. Calculator: Implement scoring logic
4. Commands: Update CLI commands
5. TUI: Add to profile view

Let's start with the model change:
[provides code]

You: Looks good. Show me the migration next.

AI: Here's the Alembic migration:
[provides migration code]
```

---

**Happy coding with AI! 🤖✨**

For more information, see:
- Research document: `docs/CLI_INTEGRATION_RESEARCH.md`
- Source code: `leadsauce/services/ai_cli.py` and `leadsauce/utils/ai_interactive.py`
