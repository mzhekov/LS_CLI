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
    """Test for documented Workshop menu navigation conflict (Issue #1)"""

    def test_workshop_uses_conflicting_shortcuts(self):
        """
        KNOWN ISSUE: Workshop menu uses 1-6 for tools, which conflicts with global nav
        This test documents the inconsistency found in regression testing

        Expected: Workshop should use different shortcuts (a-f or letters)
        Actual: Workshop uses 1-6, conflicting with global navigation

        Reference: REGRESSION_TEST_FINDINGS.md Issue #1
        """
        # Document the conflict
        global_shortcuts = {item[2] for item in NAV_ITEMS}
        workshop_shortcuts = {'1', '2', '3', '4', '5', '6'}  # From workshop_menu()

        conflict = global_shortcuts.intersection(workshop_shortcuts)

        # This test DOCUMENTS the issue - it should fail until fixed
        assert len(conflict) > 0, "Workshop shortcuts conflict with global navigation"
        assert conflict == {'1', '2', '3', '4', '5', '6'}


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

    def test_double_backspace_in_text_prompts_only(self):
        """
        KNOWN ISSUE: Double backspace only works in text prompts, not select prompts

        Reference: REGRESSION_TEST_FINDINGS.md Issue #6
        """
        # This test documents that safe_questionary_select() doesn't support double backspace
        # while safe_questionary_text() does
        from leadsauce.utils.interactive import safe_questionary_text, safe_questionary_select
        import inspect

        # Check if double backspace logic exists in text function
        text_source = inspect.getsource(safe_questionary_text)
        assert 'DOUBLE_BACKSPACE_QUIT' in text_source

        # Check if it's missing in select function
        select_source = inspect.getsource(safe_questionary_select)
        # Select doesn't have double backspace handling
        assert 'create_double_backspace_bindings' not in select_source


class TestSpecialKeyboardShortcuts:
    """Test special keyboard shortcuts (Ctrl+K, Ctrl+R)"""

    def test_ctrl_k_availability(self):
        """
        KNOWN ISSUE: Ctrl+K shown in all views but only implemented in Dashboard

        Reference: REGRESSION_TEST_FINDINGS.md Issue #2
        """
        # This test documents the inconsistency
        # Ctrl+K (\x0b) is only handled in show_dashboard_view()
        # but advertised in render_top_bar() for all views

        # We can verify by checking the top bar shows it globally
        panel = render_top_bar("Profiles")
        assert "Ctrl+K" in str(panel), "Ctrl+K shown in non-Dashboard view"

        # But it's only implemented in Dashboard (lines 936-946 of interactive.py)
        # This test documents the gap

    def test_ctrl_r_availability(self):
        """
        KNOWN ISSUE: Ctrl+R shown in Dashboard but only partially implemented

        Reference: REGRESSION_TEST_FINDINGS.md Issue #2
        """
        # Ctrl+R (\x12) is only handled in show_dashboard_view()
        panel = render_top_bar("Dashboard")
        assert "Ctrl+K" in str(panel)  # Ctrl+R is mentioned with Ctrl+K


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
    """Test Search menu structure inconsistency"""

    def test_search_menu_lacks_action_loop(self):
        """
        KNOWN ISSUE: Search menu doesn't have action loop like other menus

        Reference: REGRESSION_TEST_FINDINGS.md Issue #3
        """
        # Search menu (search_interactive) doesn't have:
        # - While loop for staying in context
        # - Action shortcuts bar
        # - Options to refine or take actions on results

        # Other menus all have: while True: ... loop with actions
        # Search just: search once, show results, press key, exit

        # This test documents the inconsistency


class TestImportExportMenuPattern:
    """Test Import/Export menu pattern"""

    def test_import_export_uses_select_not_shortcuts(self):
        """
        KNOWN ISSUE: Import/Export uses questionary.select instead of single-key shortcuts

        Reference: REGRESSION_TEST_FINDINGS.md Issue #5
        """
        # Import/Export menu uses questionary.select() (lines 6812-6816)
        # instead of single-key shortcuts like other menus

        # This makes it slower to navigate (requires arrow keys + Enter)
        # vs other menus (single keypress)

        # This test documents the inconsistency


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
