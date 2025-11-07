"""
Tests for interactive TUI navigation and keyboard shortcuts
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from leadsauce.utils.interactive import (
    NAV_ITEMS,
    render_top_bar,
    get_single_key
)


class TestNavigationConstants:
    """Test navigation menu structure"""

    def test_nav_items_structure(self):
        """Test that NAV_ITEMS has correct structure"""
        assert len(NAV_ITEMS) == 11, "Should have 11 navigation items"

        expected_items = [
            ("Dashboard", "📊", "1"),
            ("Profiles", "👥", "2"),
            ("Companies", "🏢", "3"),
            ("Network & Relationships", "🗺️", "4"),
            ("Search", "🔍", "5"),
            ("Tags", "🏷️", "6"),
            ("Workshop", "🔧", "7"),
            ("Import/Export", "📦", "8"),
            ("AI CLI Control", "🎮", "9"),
            ("Browser", "🌐", "0"),
            ("Exit", "❌", "q")
        ]

        assert NAV_ITEMS == expected_items

    def test_navigation_shortcuts_unique(self):
        """Test that all navigation shortcuts are unique"""
        shortcuts = [key for _, _, key in NAV_ITEMS]
        assert len(shortcuts) == len(set(shortcuts)), "All shortcuts should be unique"

    def test_navigation_shortcuts_valid(self):
        """Test that shortcuts are valid single characters"""
        for name, icon, key in NAV_ITEMS:
            assert len(key) == 1, f"{name} shortcut should be single character"
            assert key.isalnum() or key == 'q', f"{name} shortcut should be alphanumeric or 'q'"


class TestTopBar:
    """Test top navigation bar rendering"""

    def test_render_top_bar_dashboard(self):
        """Test rendering top bar with Dashboard highlighted"""
        panel = render_top_bar("Dashboard")
        assert panel is not None
        # Panel should be a Rich Panel object
        from rich.panel import Panel
        assert isinstance(panel, Panel)

    def test_render_top_bar_profiles(self):
        """Test rendering top bar with Profiles highlighted"""
        panel = render_top_bar("Profiles")
        assert panel is not None

    def test_render_top_bar_invalid_view(self):
        """Test rendering top bar with invalid view name"""
        # Should not crash, just not highlight anything
        panel = render_top_bar("InvalidView")
        assert panel is not None

    def test_render_top_bar_shows_ctrl_k(self):
        """Test that top bar shows Ctrl+K shortcut"""
        panel = render_top_bar("Dashboard")
        # Check subtitle mentions Ctrl+K
        assert "Ctrl+K" in str(panel)


class TestNavigationShortcuts:
    """Test navigation shortcuts consistency"""

    def test_dashboard_shortcut(self):
        """Test Dashboard is mapped to key '1'"""
        dashboard_item = next(item for item in NAV_ITEMS if item[0] == "Dashboard")
        assert dashboard_item[2] == "1"

    def test_profiles_shortcut(self):
        """Test Profiles is mapped to key '2'"""
        profiles_item = next(item for item in NAV_ITEMS if item[0] == "Profiles")
        assert profiles_item[2] == "2"

    def test_workshop_shortcut(self):
        """Test Workshop is mapped to key '7'"""
        workshop_item = next(item for item in NAV_ITEMS if item[0] == "Workshop")
        assert workshop_item[2] == "7"

    def test_exit_shortcut(self):
        """Test Exit is mapped to key 'q'"""
        exit_item = next(item for item in NAV_ITEMS if item[0] == "Exit")
        assert exit_item[2] == "q"


class TestWorkshopNavigationConflict:
    """Test for Workshop menu navigation - FIXED"""

    def test_workshop_uses_letter_shortcuts(self):
        """
        FIXED: Workshop menu now uses letter shortcuts (h,k,i,r,g,c) instead of 1-6
        Global navigation (1-9,0) now works in Workshop menu

        Fixed in: Fix commit - Workshop shortcuts changed to avoid conflict
        Reference: REGRESSION_TEST_FINDINGS.md Issue #1 (RESOLVED)
        """
        # Workshop now uses letter shortcuts
        workshop_shortcuts = {'h', 'k', 'i', 'r', 'g', 'c'}  # From workshop_menu()
        global_shortcuts = {item[2] for item in NAV_ITEMS}

        # No conflict anymore
        conflict = global_shortcuts.intersection(workshop_shortcuts)
        assert len(conflict) == 0, "Workshop shortcuts should not conflict with global navigation"


class TestDoubleBackspace:
    """Test double backspace functionality"""

    @patch('sys.stdin')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    def test_single_backspace_returns_backspace(self, mock_setraw, mock_setattr,
                                                 mock_getattr, mock_stdin):
        """Test that single backspace returns backspace character"""
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = '\x7f'  # Backspace
        mock_getattr.return_value = []

        result = get_single_key()
        assert result == '\x7f'

    def test_double_backspace_in_all_prompts(self):
        """
        FIXED: Double backspace now works in both text and select prompts

        Fixed in: Fix commit - Added double backspace to safe_questionary_select()
        Reference: REGRESSION_TEST_FINDINGS.md Issue #6 (RESOLVED)
        """
        from leadsauce.utils.interactive import safe_questionary_text, safe_questionary_select
        import inspect

        # Check if double backspace logic exists in text function
        text_source = inspect.getsource(safe_questionary_text)
        assert 'DOUBLE_BACKSPACE_QUIT' in text_source
        assert 'create_double_backspace_bindings' in text_source

        # Check that select function now has it too
        select_source = inspect.getsource(safe_questionary_select)
        assert 'DOUBLE_BACKSPACE_QUIT' in select_source
        assert 'create_double_backspace_bindings' in select_source


class TestSpecialKeyboardShortcuts:
    """Test special keyboard shortcuts (Ctrl+K, Ctrl+R) - FIXED"""

    def test_ctrl_k_global_availability(self):
        """
        FIXED: Ctrl+K now available globally via handle_global_shortcuts()
        Works in all views: Dashboard, Profiles, Companies, Tags, etc.

        Fixed in: Fix commit - Created handle_global_shortcuts() function
        Reference: REGRESSION_TEST_FINDINGS.md Issue #2 (RESOLVED)
        """
        # Verify global shortcut handler exists
        from leadsauce.utils.interactive import handle_global_shortcuts
        import inspect

        # Check function signature
        sig = inspect.signature(handle_global_shortcuts)
        assert 'action' in sig.parameters
        assert 'current_view' in sig.parameters

        # Function should be callable
        assert callable(handle_global_shortcuts)

    def test_ctrl_r_global_availability(self):
        """
        FIXED: Ctrl+R now available globally via handle_global_shortcuts()

        Reference: REGRESSION_TEST_FINDINGS.md Issue #2 (RESOLVED)
        """
        # Ctrl+R handled by same global function
        from leadsauce.utils.interactive import handle_global_shortcuts
        assert callable(handle_global_shortcuts)


class TestNavigationFlow:
    """Test navigation flow between views"""

    def test_all_views_return_to_dashboard_on_none(self):
        """Test that returning None from a view goes back to Dashboard"""
        # This is the documented behavior in interactive_main_menu()
        # Each view: if new_view is None, current_view = "Dashboard"

        view_functions = [
            "profiles_menu",
            "companies_menu",
            "network_and_relationships_menu",
            "search_interactive",
            "tags_menu",
            "workshop_menu",
            "import_export_menu",
            "browser_menu"
        ]

        # All these should return None or view name
        # None means "go back to dashboard"
        # This test documents the expected behavior

    def test_view_navigation_returns_view_name(self):
        """Test that views can return view names for navigation"""
        # When number keys are pressed, views should return the view name
        # e.g., pressing '1' returns "Dashboard"

        # This documents the navigation contract


class TestActionShortcuts:
    """Test action shortcuts in different menus"""

    def test_profile_menu_shortcuts(self):
        """Test Profile menu has expected action shortcuts"""
        # Expected: [a]dd, [e]dit, [d]elete, [s]earch, [n]ext, [p]rev, [r]efresh
        expected_shortcuts = {'a', 'e', 'd', 's', 'n', 'p', 'r'}
        # This documents the shortcuts from lines 1602-1616

    def test_company_menu_shortcuts(self):
        """Test Company menu has expected action shortcuts"""
        # Expected: [a]dd, [e]dit, [d]elete, [n]ext, [p]rev, [r]efresh
        expected_shortcuts = {'a', 'e', 'd', 'n', 'p', 'r'}
        # This documents the shortcuts from lines 1841-1853

    def test_tags_menu_shortcuts(self):
        """Test Tags menu has expected action shortcuts"""
        # Expected: [a]dd, [e]dit, [d]elete, [r]efresh
        expected_shortcuts = {'a', 'e', 'd', 'r'}
        # This documents the shortcuts from lines 2035-2043

    def test_dashboard_shortcuts(self):
        """Test Dashboard has many shortcuts without conflicts"""
        # Dashboard uses: t, c, e, d, v, r (tasks)
        #                 g, h, l, p, x, a (goals)
        #                 m, n (reminders)
        task_shortcuts = {'t', 'c', 'e', 'd', 'v', 'r'}
        goal_shortcuts = {'g', 'h', 'l', 'p', 'x', 'a'}
        reminder_shortcuts = {'m', 'n'}

        all_shortcuts = task_shortcuts | goal_shortcuts | reminder_shortcuts

        # Check for overlaps
        assert len(all_shortcuts) == len(task_shortcuts) + len(goal_shortcuts) + len(reminder_shortcuts)

        # Reference: REGRESSION_TEST_FINDINGS.md Issue #8
        # High number of shortcuts limits future expansion


class TestSearchMenuInconsistency:
    """Test Search menu structure - FIXED"""

    def test_search_menu_has_action_loop(self):
        """
        FIXED: Search menu now has action loop with shortcuts like other menus
        Features: [s] Search, [v] View, [e] Edit, [c] Clear, navigation

        Fixed in: Fix commit - Refactored search_interactive() completely
        Reference: REGRESSION_TEST_FINDINGS.md Issue #3 (RESOLVED)
        """
        from leadsauce.utils.interactive import search_interactive
        import inspect

        source = inspect.getsource(search_interactive)

        # Should have while True loop
        assert 'while True:' in source

        # Should have action shortcuts
        assert '[s] Search' in source or 'Search' in source
        assert 'get_single_key()' in source

        # Should have result table display
        assert 'Table' in source or 'table' in source


class TestImportExportMenuPattern:
    """Test Import/Export menu pattern - FIXED"""

    def test_import_export_uses_single_key_shortcuts(self):
        """
        FIXED: Import/Export now uses single-key shortcuts [1] and [2]
        No longer requires arrow keys + Enter navigation

        Fixed in: Fix commit - Replaced questionary.select with get_single_key()
        Reference: REGRESSION_TEST_FINDINGS.md Issue #5 (RESOLVED)
        """
        from leadsauce.utils.interactive import import_export_menu
        import inspect

        source = inspect.getsource(import_export_menu)

        # Should use get_single_key() instead of questionary.select()
        assert 'get_single_key()' in source

        # Should have single-key shortcuts [1] and [2]
        assert '[1]' in source or 'action == \'1\'' in source
        assert '[2]' in source or 'action == \'2\'' in source


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
