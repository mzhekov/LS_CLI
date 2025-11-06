"""
Keyboard shortcut support for quick menu navigation

Provides Ctrl+number shortcuts for instant menu switching.
Note: Uses signals for cross-thread communication.
"""

import threading
import signal
from typing import Optional, Callable, Dict


class MenuShortcutHandler:
    """Handles menu navigation shortcuts"""

    _instance = None
    _lock = threading.Lock()

    # Menu mapping for Ctrl+number
    MENU_SHORTCUTS = {
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

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.target_menu: Optional[str] = None
        self.switch_requested = threading.Event()

    def request_switch(self, menu_name: str):
        """Request a menu switch

        Args:
            menu_name: Name of menu to switch to
        """
        self.target_menu = menu_name
        self.switch_requested.set()

    def check_switch_request(self) -> Optional[str]:
        """Check if a menu switch was requested

        Returns:
            Menu name if switch requested, None otherwise
        """
        if self.switch_requested.is_set():
            menu = self.target_menu
            self.target_menu = None
            self.switch_requested.clear()
            return menu
        return None

    def get_shortcut_help(self) -> str:
        """Get help text for shortcuts"""
        return "[bold]Quick Switch:[/bold] Ctrl+1-9,0 for instant menu access"


# Global instance
menu_shortcut_handler = MenuShortcutHandler()
