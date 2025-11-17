"""
Logging configuration and utilities for LeadSauce.

This module provides a centralized logging setup with file and console handlers,
dynamic log level management, and debug mode toggling.
"""

import logging
import os
from pathlib import Path
from typing import Optional
import sys

from .config import get_config
from .constants import LOG_DIR, LOG_FILE


class DebugLogger:
    """Centralized logger for LeadSauce with debug mode support."""

    _instance: Optional['DebugLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern to ensure only one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger (only once)."""
        if not self._initialized:
            self.logger = logging.getLogger('leadsauce')
            self.file_handler: Optional[logging.FileHandler] = None
            self.console_handler: Optional[logging.StreamHandler] = None
            self._setup_logger()
            DebugLogger._initialized = True

    def _setup_logger(self):
        """Set up logging handlers and formatters."""
        config = get_config()

        # Create logs directory if it doesn't exist
        log_dir = Path(LOG_DIR).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set base logger level to DEBUG to allow handlers to filter
        self.logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.logger.handlers.clear()

        # File handler - always logs at DEBUG level
        log_file = Path(LOG_FILE).expanduser()
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)

        # Detailed format for file logs
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(file_formatter)
        self.logger.addHandler(self.file_handler)

        # Console handler - respects config log level
        self.console_handler = logging.StreamHandler(sys.stderr)
        log_level = config.get('logging.level', 'INFO')
        self.console_handler.setLevel(getattr(logging, log_level))

        # Simpler format for console
        console_formatter = logging.Formatter(
            fmt='[%(levelname)s] %(message)s'
        )
        self.console_handler.setFormatter(console_formatter)
        self.logger.addHandler(self.console_handler)

        # Log initial setup
        self.logger.debug(f"Logger initialized - File: {log_file}, Level: {log_level}")

    def set_level(self, level: str):
        """
        Dynamically change the logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        config = get_config()
        config.set('logging.level', level.upper())

        # Update console handler level
        if self.console_handler:
            self.console_handler.setLevel(getattr(logging, level.upper()))

        self.logger.debug(f"Log level changed to {level.upper()}")

    def toggle_debug(self) -> str:
        """
        Toggle between DEBUG and INFO logging levels.

        Returns:
            The new logging level
        """
        config = get_config()
        current_level = config.get('logging.level', 'INFO')
        new_level = 'INFO' if current_level == 'DEBUG' else 'DEBUG'
        self.set_level(new_level)
        return new_level

    def get_level(self) -> str:
        """Get the current logging level."""
        config = get_config()
        return config.get('logging.level', 'INFO')

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance.

        Args:
            name: Optional name for the logger (creates a child logger)

        Returns:
            Logger instance
        """
        if name:
            return self.logger.getChild(name)
        return self.logger

    def log_operation(self, operation: str, details: dict = None):
        """
        Log an operation with structured details.

        Args:
            operation: Name of the operation
            details: Optional dictionary of operation details
        """
        if details:
            detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
            self.logger.debug(f"OPERATION: {operation} | {detail_str}")
        else:
            self.logger.debug(f"OPERATION: {operation}")

    def log_db_operation(self, operation: str, table: str, details: dict = None):
        """
        Log a database operation.

        Args:
            operation: Type of operation (SELECT, INSERT, UPDATE, DELETE)
            table: Database table name
            details: Optional query details
        """
        self.log_operation(f"DB.{operation}", {"table": table, **(details or {})})

    def log_api_call(self, method: str, endpoint: str, status: int = None):
        """
        Log an API call.

        Args:
            method: HTTP method
            endpoint: API endpoint
            status: HTTP status code
        """
        details = {"method": method, "endpoint": endpoint}
        if status:
            details["status"] = status
        self.log_operation("API_CALL", details)

    def get_log_file_path(self) -> Path:
        """Get the path to the log file."""
        return Path(LOG_FILE).expanduser()


# Global logger instance
_debug_logger: Optional[DebugLogger] = None


def setup_logging():
    """Initialize the global logging system."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional name for the logger

    Returns:
        Logger instance
    """
    if _debug_logger is None:
        setup_logging()
    return _debug_logger.get_logger(name)


def toggle_debug_mode() -> str:
    """
    Toggle debug mode on/off.

    Returns:
        The new logging level
    """
    if _debug_logger is None:
        setup_logging()
    return _debug_logger.toggle_debug()


def get_log_level() -> str:
    """Get the current log level."""
    if _debug_logger is None:
        setup_logging()
    return _debug_logger.get_level()


def log_operation(operation: str, details: dict = None):
    """
    Log an operation (convenience function).

    Args:
        operation: Operation name
        details: Optional details dictionary
    """
    if _debug_logger is None:
        setup_logging()
    _debug_logger.log_operation(operation, details)
