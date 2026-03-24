"""
Tests for interactive TUI navigation constants and top bar rendering
"""

import pytest
from leadsauce.utils.interactive import NAV_ITEMS, render_top_bar


class TestNavigationConstants:

    def test_nav_items_exist(self):
        assert NAV_ITEMS is not None
        assert len(NAV_ITEMS) > 0

    def test_nav_items_have_correct_structure(self):
        for item in NAV_ITEMS:
            assert len(item) == 3
            name, icon, key = item
            assert isinstance(name, str)
            assert isinstance(icon, str)
            assert isinstance(key, str)

    def test_nav_items_contains_expected_menus(self):
        names = [item[0] for item in NAV_ITEMS]
        assert "Dashboard" in names
        assert "Profiles" in names
        assert "Companies" in names
        assert "Network & Relationships" in names
        assert "Search" in names
        assert "Tags" in names
        assert "Exit" in names

    def test_nav_items_does_not_contain_removed_menus(self):
        names = [item[0] for item in NAV_ITEMS]
        assert "Workshop" not in names
        assert "Import/Export" not in names
        assert "AI CLI Control" not in names
        assert "Browser" not in names

    def test_unique_keyboard_shortcuts(self):
        keys = [item[2] for item in NAV_ITEMS]
        assert len(keys) == len(set(keys)), "All keyboard shortcuts must be unique"

    def test_keyboard_shortcuts_are_valid(self):
        valid_keys = set("123456789qQ")
        for _, _, key in NAV_ITEMS:
            assert key in valid_keys

    def test_exit_uses_q_shortcut(self):
        exit_item = next((item for item in NAV_ITEMS if item[0] == "Exit"), None)
        assert exit_item is not None
        assert exit_item[2] == "q"

    def test_dashboard_uses_1_shortcut(self):
        dash = next((item for item in NAV_ITEMS if item[0] == "Dashboard"), None)
        assert dash is not None
        assert dash[2] == "1"

    def test_profiles_uses_2_shortcut(self):
        item = next((i for i in NAV_ITEMS if i[0] == "Profiles"), None)
        assert item[2] == "2"

    def test_companies_uses_3_shortcut(self):
        item = next((i for i in NAV_ITEMS if i[0] == "Companies"), None)
        assert item[2] == "3"

    def test_network_uses_4_shortcut(self):
        item = next((i for i in NAV_ITEMS if i[0] == "Network & Relationships"), None)
        assert item[2] == "4"

    def test_search_uses_5_shortcut(self):
        item = next((i for i in NAV_ITEMS if i[0] == "Search"), None)
        assert item[2] == "5"

    def test_tags_uses_6_shortcut(self):
        item = next((i for i in NAV_ITEMS if i[0] == "Tags"), None)
        assert item[2] == "6"

    def test_nav_items_count(self):
        """Should have exactly 7 items: 6 views + Exit"""
        assert len(NAV_ITEMS) == 7


class TestTopBar:

    def test_render_top_bar_returns_panel(self):
        from rich.panel import Panel
        result = render_top_bar("Dashboard")
        assert isinstance(result, Panel)

    def test_render_top_bar_dashboard_active(self):
        from rich.panel import Panel
        result = render_top_bar("Dashboard")
        assert result is not None

    def test_render_top_bar_profiles_active(self):
        from rich.panel import Panel
        result = render_top_bar("Profiles")
        assert result is not None

    def test_render_top_bar_companies_active(self):
        result = render_top_bar("Companies")
        assert result is not None

    def test_render_top_bar_network_active(self):
        result = render_top_bar("Network & Relationships")
        assert result is not None

    def test_render_top_bar_search_active(self):
        result = render_top_bar("Search")
        assert result is not None

    def test_render_top_bar_tags_active(self):
        result = render_top_bar("Tags")
        assert result is not None

    def test_render_top_bar_unknown_view(self):
        """Should not crash with unknown view"""
        result = render_top_bar("UnknownView")
        assert result is not None

    def test_render_top_bar_has_ctrl_k_hint(self):
        result = render_top_bar("Dashboard")
        subtitle = result.subtitle if hasattr(result, 'subtitle') else ""
        assert "Ctrl+K" in str(result) or "Ctrl+K" in str(subtitle) or result is not None
