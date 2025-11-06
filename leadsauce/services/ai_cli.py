"""AI CLI Integration Service

This module provides integration with AI CLI tools like Claude Code, Codex CLI,
and other coding assistants. It uses subprocess to communicate with these tools
without requiring API integration.
"""

import subprocess
import shlex
from typing import Optional, Dict, List, Tuple
from pathlib import Path


class AICLIError(Exception):
    """Base exception for AI CLI integration"""
    pass


class ToolNotInstalledError(AICLIError):
    """Raised when AI CLI tool is not installed"""
    pass


class ToolTimeoutError(AICLIError):
    """Raised when AI CLI tool times out"""
    pass


class AICLIService:
    """Service for interacting with AI CLI tools"""

    SUPPORTED_TOOLS = {
        'claude': {
            'command': 'claude',
            'name': 'Claude Code',
            'install_cmd': 'npm install -g @anthropic-ai/claude-code',
            'test_args': ['--version']
        },
        'codex': {
            'command': 'codex',
            'name': 'Codex CLI',
            'install_cmd': 'Follow instructions at https://github.com/openai/codex',
            'test_args': ['--version']
        },
        'aider': {
            'command': 'aider',
            'name': 'Aider',
            'install_cmd': 'pip install aider-chat',
            'test_args': ['--version']
        }
    }

    def __init__(self, default_tool: str = 'claude', timeout: int = 300):
        """Initialize AI CLI service

        Args:
            default_tool: Default AI tool to use (claude, codex, aider)
            timeout: Default timeout for commands in seconds
        """
        self.default_tool = default_tool
        self.timeout = timeout

    @classmethod
    def is_installed(cls, tool: str) -> bool:
        """Check if an AI CLI tool is installed

        Args:
            tool: Tool identifier (claude, codex, aider)

        Returns:
            True if tool is installed and accessible
        """
        if tool not in cls.SUPPORTED_TOOLS:
            return False

        tool_config = cls.SUPPORTED_TOOLS[tool]
        command = tool_config['command']
        test_args = tool_config.get('test_args', ['--version'])

        try:
            result = subprocess.run(
                [command] + test_args,
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    @classmethod
    def get_installed_tools(cls) -> List[Dict[str, str]]:
        """Get list of installed AI CLI tools

        Returns:
            List of dicts with tool info: {id, name, command, installed}
        """
        tools = []
        for tool_id, config in cls.SUPPORTED_TOOLS.items():
            tools.append({
                'id': tool_id,
                'name': config['name'],
                'command': config['command'],
                'installed': cls.is_installed(tool_id)
            })
        return tools

    def query(
        self,
        prompt: str,
        tool: Optional[str] = None,
        files: Optional[List[str]] = None,
        working_dir: Optional[str] = None
    ) -> str:
        """Send a query to an AI CLI tool

        Args:
            prompt: The question/prompt to send
            tool: Tool to use (defaults to self.default_tool)
            files: Optional list of files to include as context
            working_dir: Optional working directory for the command

        Returns:
            Response from the AI tool

        Raises:
            ToolNotInstalledError: If the tool is not installed
            ToolTimeoutError: If the command times out
            AICLIError: For other errors
        """
        tool = tool or self.default_tool

        if not self.is_installed(tool):
            raise ToolNotInstalledError(
                f"{self.SUPPORTED_TOOLS[tool]['name']} is not installed. "
                f"Install with: {self.SUPPORTED_TOOLS[tool]['install_cmd']}"
            )

        try:
            cmd = self._build_command(tool, prompt, files)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=working_dir
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise AICLIError(f"AI tool error: {error_msg}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise ToolTimeoutError(
                f"AI tool timed out after {self.timeout} seconds. "
                "Try a simpler query or increase timeout."
            )
        except Exception as e:
            if isinstance(e, (ToolNotInstalledError, ToolTimeoutError, AICLIError)):
                raise
            raise AICLIError(f"Unexpected error: {str(e)}")

    def _build_command(
        self,
        tool: str,
        prompt: str,
        files: Optional[List[str]] = None
    ) -> List[str]:
        """Build command line for AI tool

        Args:
            tool: Tool identifier
            prompt: User prompt
            files: Optional list of files

        Returns:
            Command as list of strings
        """
        tool_config = self.SUPPORTED_TOOLS[tool]
        cmd = [tool_config['command']]

        if tool == 'claude':
            # Claude Code: claude "prompt"
            cmd.append(prompt)
            if files:
                for file in files:
                    cmd.extend(['--file', file])

        elif tool == 'codex':
            # Codex: codex "prompt"
            cmd.append(prompt)

        elif tool == 'aider':
            # Aider: aider --message "prompt"
            cmd.extend(['--message', prompt, '--no-auto-commits'])
            if files:
                cmd.extend(files)

        return cmd

    @classmethod
    def get_tool_info(cls, tool: str) -> Dict[str, str]:
        """Get information about a specific tool

        Args:
            tool: Tool identifier

        Returns:
            Dict with tool information
        """
        if tool not in cls.SUPPORTED_TOOLS:
            return {
                'id': tool,
                'name': 'Unknown',
                'installed': False,
                'error': f'Tool "{tool}" is not supported'
            }

        config = cls.SUPPORTED_TOOLS[tool]
        return {
            'id': tool,
            'name': config['name'],
            'command': config['command'],
            'install_cmd': config['install_cmd'],
            'installed': cls.is_installed(tool)
        }

    def check_health(self) -> Dict[str, any]:
        """Check health of AI CLI integration

        Returns:
            Dict with health status information
        """
        installed_tools = self.get_installed_tools()
        installed_count = sum(1 for t in installed_tools if t['installed'])

        return {
            'healthy': installed_count > 0,
            'default_tool': self.default_tool,
            'default_tool_installed': self.is_installed(self.default_tool),
            'installed_tools': [t['id'] for t in installed_tools if t['installed']],
            'total_installed': installed_count,
            'total_available': len(self.SUPPORTED_TOOLS)
        }
