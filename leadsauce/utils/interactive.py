"""
Interactive TUI for LeadSauce CLI with top bar navigation
"""

import time
import questionary
from questionary import Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.layout import Layout
from rich.text import Text
from collections import defaultdict
from leadsauce.utils.db import get_session
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag
from leadsauce.utils.constants import SENIORITY_LEVELS, GENERATION_TYPES
from leadsauce.utils.validators import validate_email, validate_phone, parse_tags

console = Console()

# Custom style for questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#2196f3 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#4caf50'),
    ('separator', 'fg:#cc5454'),
    ('instruction', 'fg:#858585'),
    ('text', ''),
])

# Navigation menu items with keyboard shortcuts
NAV_ITEMS = [
    ("Dashboard", "📊", "1"),
    ("Profiles", "👥", "2"),
    ("Companies", "🏢", "3"),
    ("Relationships", "🔗", "4"),
    ("Network Map", "🗺️", "5"),
    ("Search", "🔍", "6"),
    ("Tags", "🏷️", "7"),
    ("Exit", "❌", "q")
]


def render_top_bar(current_view="Dashboard"):
    """Render the interactive top navigation bar with keyboard shortcuts"""
    nav_text = Text()

    for i, (name, icon, key) in enumerate(NAV_ITEMS):
        if i > 0:
            nav_text.append(" │ ", style="dim")

        if name == current_view:
            nav_text.append(f"{icon} ", style="bold cyan")
            nav_text.append(f"[{key}]", style="bold yellow")
            nav_text.append(f" {name}", style="bold cyan on #1a1a1a")
        else:
            nav_text.append(f"{icon} ", style="white")
            nav_text.append(f"[{key}]", style="dim yellow")
            nav_text.append(f" {name}", style="white")

    return Panel(nav_text, style="cyan", box=box.SIMPLE, subtitle="[dim]Press number keys to navigate[/]")


def interactive_main_menu():
    """Main interactive menu with top bar navigation and dashboard as main screen"""
    current_view = "Dashboard"

    while True:
        console.clear()

        # Show top bar
        console.print(render_top_bar(current_view))
        console.print()

        # Show current view content
        if current_view == "Dashboard":
            show_dashboard_view()
        elif current_view == "Profiles":
            profiles_menu()
            current_view = "Dashboard"  # Return to dashboard after
            continue
        elif current_view == "Companies":
            companies_menu()
            current_view = "Dashboard"
            continue
        elif current_view == "Relationships":
            relationships_menu()
            current_view = "Dashboard"
            continue
        elif current_view == "Network Map":
            show_network_map()
            current_view = "Dashboard"
            continue
        elif current_view == "Search":
            search_interactive()
            current_view = "Dashboard"
            continue
        elif current_view == "Tags":
            tags_menu()
            current_view = "Dashboard"
            continue
        elif current_view == "Exit":
            console.print("\n[cyan]Goodbye! 👋[/]\n")
            break

        # Navigation menu at bottom - allow both keyboard shortcuts and arrow key selection
        console.print()
        console.print("[dim]Navigation:[/]")
        console.print("[dim]  • Type a number (1-6) or 'q' to quit[/]")
        console.print("[dim]  • Press Enter (empty) to use arrow keys[/]")
        console.print()

        # Create a simple text prompt that accepts keyboard shortcuts
        nav_input = questionary.text(
            "Quick nav (or Enter for menu):",
            style=custom_style,
            default=""
        ).ask()

        if nav_input is None:
            # User pressed Ctrl+C
            break

        nav_input = nav_input.strip()

        # Map keyboard shortcuts to views
        shortcut_map = {key: name for name, icon, key in NAV_ITEMS}

        if nav_input in shortcut_map:
            # Direct keyboard shortcut
            current_view = shortcut_map[nav_input]
        elif nav_input == "":
            # Empty input - show arrow key menu
            nav_choices = [f"{icon} [{key}] {name}" for name, icon, key in NAV_ITEMS]

            action = questionary.select(
                "Navigate to:",
                choices=nav_choices,
                style=custom_style
            ).ask()

            if not action:
                break

            # Extract view name from selection
            for name, icon, key in NAV_ITEMS:
                if action == f"{icon} [{key}] {name}":
                    current_view = name
                    break
        else:
            # Invalid input
            console.print(f"[yellow]Invalid option '{nav_input}'. Use 1-6 or q[/]")
            import time
            time.sleep(1.5)


def show_dashboard_view():
    """Show the main dashboard with statistics and quick actions"""
    session = get_session()

    # Get statistics
    total_profiles = session.query(Profile).count()
    total_companies = session.query(Company).count()
    total_tags = session.query(Tag).count()

    # Get recent profiles
    recent_profiles = session.query(Profile).order_by(Profile.created_at.desc()).limit(5).all()

    # Create statistics panel
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan bold", justify="right")
    stats_table.add_column(style="white")

    stats_table.add_row("Profiles:", str(total_profiles))
    stats_table.add_row("Companies:", str(total_companies))
    stats_table.add_row("Tags:", str(total_tags))

    console.print(Panel(stats_table, title="[bold yellow]📊 Overview[/]", border_style="yellow"))
    console.print()

    # Recent profiles
    if recent_profiles:
        profiles_table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
        profiles_table.add_column("Name", style="cyan")
        profiles_table.add_column("Seniority", style="blue")
        profiles_table.add_column("Company", style="green")

        for p in recent_profiles:
            profiles_table.add_row(
                p.name,
                p.seniority.title(),
                p.company.name if p.company else "-"
            )

        console.print(Panel(profiles_table, title="[bold cyan]Recent Profiles[/]", border_style="cyan"))
    else:
        console.print(Panel(
            "[yellow]No profiles yet. Press [2] to add your first contact![/]",
            border_style="yellow"
        ))

    # Quick actions hint
    console.print()
    console.print(Panel(
        "[bold cyan]Quick Actions:[/]\n"
        "[dim]Press [2] for Profiles • [3] for Companies • [4] for Network Map[/]",
        border_style="cyan",
        box=box.SIMPLE
    ))

    session.close()


def profiles_menu():
    """Show profiles list with action shortcuts in top bar"""
    session = get_session()

    while True:
        console.clear()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[a] Add", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[s] Search", style="cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[r] Refresh", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[Enter] Back", style="dim white")

        console.print(Panel(
            actions_text,
            title="[bold cyan]👥 Profiles[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Get profiles
        profiles = session.query(Profile).order_by(Profile.name).all()

        if profiles:
            # Display profiles list
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Name", style="cyan")
            table.add_column("Seniority", style="blue")
            table.add_column("Company", style="green")
            table.add_column("Tags", style="yellow")

            for idx, p in enumerate(profiles, 1):
                company = p.company.name if p.company else "-"
                tags = ", ".join([t.name for t in p.tags[:2]]) if p.tags else "-"
                if len(p.tags) > 2:
                    tags += "..."
                table.add_row(str(idx), p.name, p.seniority.title(), company, tags)

            console.print(table)
            console.print(f"\n[dim]{len(profiles)} profile(s) total[/]")
        else:
            console.print(Panel(
                "[yellow]No profiles yet. Press 'a' to add your first contact![/]",
                border_style="yellow"
            ))

        console.print()
        console.print("[dim]Tip: Just press Enter to go back (or type 1)[/]")
        console.print()

        # Action prompt
        action = questionary.text(
            "Action ([a]dd/[e]dit/[s]earch/[#] view):",
            style=custom_style
        ).ask()

        if action is None:
            # Ctrl+C pressed
            break

        action = action.strip().lower()

        # Empty input = back to dashboard
        if action == '' or action == '1':
            break

        if action == 'a':
            add_profile_interactive()
        elif action == 'e':
            # Edit a profile - show selection menu
            if not profiles:
                console.print("[yellow]No profiles to edit[/]")
                import time
                time.sleep(1)
                continue

            # Quick selection for edit
            profile_choices = [{'name': f"{idx+1}. {p.name}", 'value': p.id} for idx, p in enumerate(profiles)]
            profile_choices.append({'name': '← Cancel', 'value': None})

            profile_id = questionary.select(
                "Select profile to edit:",
                choices=profile_choices,
                style=custom_style
            ).ask()

            if profile_id:
                profile = session.query(Profile).filter(Profile.id == profile_id).first()
                if profile:
                    edit_profile_interactive(profile, session)
        elif action == 's':
            search_interactive()
        elif action == 'r':
            continue  # Refresh
        elif action.isdigit():
            # View profile by number
            idx = int(action) - 1
            if 0 <= idx < len(profiles):
                show_profile_details(profiles[idx].id, session)
            else:
                console.print(f"[yellow]Invalid number. Choose 1-{len(profiles)}[/]")
                questionary.press_any_key_to_continue().ask()
        else:
            console.print(f"[yellow]Invalid action '{action}'[/]")
            import time
            time.sleep(1)

    session.close()


def companies_menu():
    """Show companies list with action shortcuts in top bar"""
    session = get_session()

    while True:
        console.clear()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[a] Add", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[r] Refresh", style="cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[Enter] Back", style="dim white")

        console.print(Panel(
            actions_text,
            title="[bold cyan]🏢 Companies[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Get companies
        companies = session.query(Company).order_by(Company.name).all()

        if companies:
            # Display companies list
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Name", style="cyan")
            table.add_column("Industry", style="blue")
            table.add_column("Profiles", justify="right", style="green")
            table.add_column("Location", style="yellow")

            for idx, c in enumerate(companies, 1):
                table.add_row(
                    str(idx),
                    c.name,
                    c.industry or "-",
                    str(len(c.profiles)),
                    c.location or "-"
                )

            console.print(table)
            console.print(f"\n[dim]{len(companies)} company(ies) total[/]")
        else:
            console.print(Panel(
                "[yellow]No companies yet. Press 'a' to add one![/]",
                border_style="yellow"
            ))

        console.print()
        console.print("[dim]Tip: Just press Enter to go back (or type 1)[/]")
        console.print()

        # Action prompt
        action = questionary.text(
            "Action ([a]dd/[e]dit/[#] view company):",
            style=custom_style
        ).ask()

        if action is None:
            # Ctrl+C pressed
            break

        action = action.strip().lower()

        # Empty input = back to dashboard
        if action == '' or action == '1':
            break

        if action == 'a':
            add_company_interactive()
        elif action == 'e':
            edit_company_menu()
        elif action == 'r':
            continue  # Refresh
        elif action.isdigit():
            # View company by number
            idx = int(action) - 1
            if 0 <= idx < len(companies):
                show_company_details(companies[idx], session)
            else:
                console.print(f"[yellow]Invalid number. Choose 1-{len(companies)}[/]")
                questionary.press_any_key_to_continue().ask()
        else:
            console.print(f"[yellow]Invalid action '{action}'[/]")
            import time
            time.sleep(1)

    session.close()


def tags_menu():
    """Show tags list with action shortcuts in top bar"""
    session = get_session()

    while True:
        console.clear()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[a] Add", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[d] Delete", style="red")
        actions_text.append(" • ", style="dim")
        actions_text.append("[r] Refresh", style="cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[Enter] Back", style="dim white")

        console.print(Panel(
            actions_text,
            title="[bold cyan]🏷️  Tags[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Get tags
        tags = session.query(Tag).order_by(Tag.name).all()

        if tags:
            # Display tags list
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Tag", style="cyan")
            table.add_column("Color", style="white")
            table.add_column("Profiles", justify="right", style="green")

            for idx, tag in enumerate(tags, 1):
                count = len(tag.profiles)
                color_display = f"[{tag.color or 'white'}]●[/]" if tag.color else "-"
                table.add_row(str(idx), tag.name, color_display, str(count))

            console.print(table)
            console.print(f"\n[dim]{len(tags)} tag(s) total[/]")
        else:
            console.print(Panel(
                "[yellow]No tags yet. Press 'a' to add one![/]",
                border_style="yellow"
            ))

        console.print()
        console.print("[dim]Tip: Just press Enter to go back (or type 1)[/]")
        console.print()

        # Action prompt
        action = questionary.text(
            "Action ([a]dd/[e]dit/[d]elete):",
            style=custom_style
        ).ask()

        if action is None:
            # Ctrl+C pressed
            break

        action = action.strip().lower()

        # Empty input = back to dashboard
        if action == '' or action == '1':
            break

        if action == 'a':
            add_tag_interactive()
        elif action == 'e':
            edit_tag_interactive()
        elif action == 'd':
            delete_tag_interactive()
        elif action == 'r':
            continue  # Refresh
        else:
            console.print(f"[yellow]Invalid action '{action}'[/]")
            import time
            time.sleep(1)

    session.close()


def relationships_menu():
    """Show relationships list with action shortcuts in top bar"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship

    session = get_session()
    view_filter = 'all'  # 'all', 'profile', 'company'

    while True:
        console.clear()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[a] Add", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[d] Delete", style="red")
        actions_text.append(" • ", style="dim")
        actions_text.append("[p] Profile Only", style="cyan" if view_filter == 'profile' else "dim")
        actions_text.append(" • ", style="dim")
        actions_text.append("[c] Company Only", style="cyan" if view_filter == 'company' else "dim")
        actions_text.append(" • ", style="dim")
        actions_text.append("[r] Refresh", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[Enter] Back", style="dim white")

        filter_label = ""
        if view_filter == 'profile':
            filter_label = " (Profile Only)"
        elif view_filter == 'company':
            filter_label = " (Company Only)"

        console.print(Panel(
            actions_text,
            title=f"[bold cyan]🔗 Relationships{filter_label}[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Get relationships
        profile_rels = session.query(ProfileRelationship).all()
        company_rels = session.query(CompanyRelationship).all()

        # Apply filter
        display_profile = view_filter in ['all', 'profile']
        display_company = view_filter in ['all', 'company']

        has_data = (display_profile and profile_rels) or (display_company and company_rels)

        if has_data:
            # Display relationships
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Type", style="magenta", width=8)
            table.add_column("From", style="cyan")
            table.add_column("→", style="yellow", width=3)
            table.add_column("Relationship", style="yellow")
            table.add_column("To", style="cyan")
            table.add_column("Status", style="white")

            idx = 1

            # Add profile relationships
            if display_profile:
                for rel in profile_rels:
                    arrow = "↔" if rel.bidirectional else "→"
                    status_color = "green" if rel.status == "Good" else "red" if rel.status == "Bad" else "dim"
                    table.add_row(
                        str(idx),
                        "👥 Person",
                        rel.from_profile.name,
                        arrow,
                        rel.relationship_type,
                        rel.to_profile.name,
                        f"[{status_color}]{rel.status}[/]"
                    )
                    idx += 1

            # Add company relationships
            if display_company:
                for rel in company_rels:
                    arrow = "↔" if rel.bidirectional else "→"
                    status_color = "green" if rel.status == "Good" else "red" if rel.status == "Bad" else "dim"
                    table.add_row(
                        str(idx),
                        "🏢 Company",
                        rel.from_company.name,
                        arrow,
                        rel.relationship_type,
                        rel.to_company.name,
                        f"[{status_color}]{rel.status}[/]"
                    )
                    idx += 1

            console.print(table)

            profile_count = len(profile_rels) if display_profile else 0
            company_count = len(company_rels) if display_company else 0
            total = profile_count + company_count

            if view_filter == 'all':
                console.print(f"\n[dim]{total} relationship(s) total ({profile_count} profile, {company_count} company)[/]")
            else:
                console.print(f"\n[dim]{total} relationship(s) shown[/]")
        else:
            console.print(Panel(
                "[yellow]No relationships yet. Press 'a' to create your first relationship![/]",
                border_style="yellow"
            ))

        console.print()
        console.print("[dim]Tip: Just press Enter to go back (or type 1)[/]")
        console.print()

        # Action prompt
        action = questionary.text(
            "Action ([a]dd/[e]dit/[d]elete/[p]rofile/[c]ompany):",
            style=custom_style
        ).ask()

        if action is None:
            # Ctrl+C pressed
            break

        action = action.strip().lower()

        # Empty input = back to dashboard
        if action == '' or action == '1':
            break

        if action == 'a':
            # Add relationship - ask which type
            rel_type = questionary.select(
                "Add which type of relationship?",
                choices=[
                    "👥 Profile Relationship",
                    "🏢 Company Relationship",
                    "← Cancel"
                ],
                style=custom_style
            ).ask()

            if rel_type == "👥 Profile Relationship":
                add_profile_relationship()
            elif rel_type == "🏢 Company Relationship":
                add_company_relationship()

        elif action == 'e':
            # Edit relationship - ask which type
            rel_type = questionary.select(
                "Edit which type of relationship?",
                choices=[
                    "👥 Profile Relationship",
                    "🏢 Company Relationship",
                    "← Cancel"
                ],
                style=custom_style
            ).ask()

            if rel_type == "👥 Profile Relationship":
                edit_profile_relationship()
            elif rel_type == "🏢 Company Relationship":
                edit_company_relationship()

        elif action == 'd':
            # Delete relationship - ask which type
            rel_type = questionary.select(
                "Delete which type of relationship?",
                choices=[
                    "👥 Profile Relationship",
                    "🏢 Company Relationship",
                    "← Cancel"
                ],
                style=custom_style
            ).ask()

            if rel_type == "👥 Profile Relationship":
                delete_profile_relationship()
            elif rel_type == "🏢 Company Relationship":
                delete_company_relationship()

        elif action == 'p':
            view_filter = 'profile' if view_filter != 'profile' else 'all'

        elif action == 'c':
            view_filter = 'company' if view_filter != 'company' else 'all'

        elif action == 'r':
            # Refresh - just loop again
            continue
        else:
            console.print("[yellow]Invalid action. Try again.[/]")
            time.sleep(1)

    session.close()


def show_network_map():
    """Show visual network graph of relationships between profiles and companies"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship
    import math
    import random

    session = get_session()

    profiles = session.query(Profile).all()
    companies = session.query(Company).all()
    profile_relationships = session.query(ProfileRelationship).all()
    company_relationships = session.query(CompanyRelationship).all()

    if not profiles and not companies:
        console.print(Panel(
            "[yellow]No data to visualize. Add some profiles and companies first![/]",
            border_style="yellow"
        ))
        questionary.press_any_key_to_continue("Press any key to continue...").ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold cyan]🗺️  Network Relationship Map[/]\n"
        "[dim]Visual representation of connections[/]",
        border_style="cyan"
    ))
    console.print()

    # Build network structure
    nodes = []
    node_map = {}  # id -> node index
    edges = []

    # Add profile nodes
    for profile in profiles:
        node_id = f"p_{profile.id}"
        node_idx = len(nodes)
        node_map[node_id] = node_idx
        nodes.append({
            'id': node_id,
            'name': profile.name[:20],  # Truncate long names
            'type': 'profile',
            'entity': profile
        })

    # Add company nodes
    for company in companies:
        node_id = f"c_{company.id}"
        node_idx = len(nodes)
        node_map[node_id] = node_idx
        nodes.append({
            'id': node_id,
            'name': company.name[:20],
            'type': 'company',
            'entity': company
        })

    # Add profile relationships as edges
    for rel in profile_relationships:
        from_id = f"p_{rel.from_profile_id}"
        to_id = f"p_{rel.to_profile_id}"
        if from_id in node_map and to_id in node_map:
            edges.append({
                'from': node_map[from_id],
                'to': node_map[to_id],
                'type': rel.relationship_type,
                'status': rel.status,
                'bidirectional': rel.bidirectional
            })

    # Add company relationships as edges
    for rel in company_relationships:
        from_id = f"c_{rel.from_company_id}"
        to_id = f"c_{rel.to_company_id}"
        if from_id in node_map and to_id in node_map:
            edges.append({
                'from': node_map[from_id],
                'to': node_map[to_id],
                'type': rel.relationship_type,
                'status': rel.status,
                'bidirectional': rel.bidirectional
            })

    # Add profile-company edges (employment)
    for profile in profiles:
        if profile.company_id:
            from_id = f"p_{profile.id}"
            to_id = f"c_{profile.company_id}"
            if from_id in node_map and to_id in node_map:
                edges.append({
                    'from': node_map[from_id],
                    'to': node_map[to_id],
                    'type': 'works_at',
                    'status': 'Good',
                    'bidirectional': False
                })

    # Simple circular layout algorithm
    width = 100  # Increased to accommodate labels
    height = 35
    center_x = width // 2
    center_y = height // 2

    # Calculate radius based on number of nodes
    radius = min(width // 2 - 15, height // 2 - 3)

    # Position nodes in a circle
    positions = []
    angles = []
    for i, node in enumerate(nodes):
        angle = (2 * math.pi * i) / len(nodes) if len(nodes) > 0 else 0
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        positions.append((x, y))
        angles.append(angle)

    # Create canvas
    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    # Draw edges first (so nodes appear on top)
    for edge in edges:
        from_pos = positions[edge['from']]
        to_pos = positions[edge['to']]

        # Simple line drawing using Bresenham-like algorithm
        x0, y0 = from_pos
        x1, y1 = to_pos

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        # Draw line
        x, y = x0, y0
        steps = 0
        max_steps = width + height  # Prevent infinite loops

        while steps < max_steps:
            if 0 <= y < height and 0 <= x < width:
                # Choose line character based on status
                if edge['type'] == 'works_at':
                    char = '·'  # Dotted for employment
                elif edge['bidirectional']:
                    char = '═'  # Double line for bidirectional
                else:
                    char = '─'  # Single line

                if canvas[y][x] == ' ':
                    canvas[y][x] = char

            if x == x1 and y == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

            steps += 1

    # Draw nodes with labels (profiles and companies)
    for i, (node, (x, y), angle) in enumerate(zip(nodes, positions, angles)):
        if 0 <= y < height and 0 <= x < width:
            # Mark node position
            if node['type'] == 'profile':
                canvas[y][x] = '👤'
            else:
                canvas[y][x] = '🏢'

            # Add label next to node
            # Truncate name to 10 characters
            label = node['name'][:10]

            # Determine label position based on angle (position around circle)
            # Right side (0 to 45 degrees or 315 to 360)
            if (angle >= 0 and angle < math.pi / 4) or (angle >= 7 * math.pi / 4):
                label_x = x + 2
                label_y = y
            # Top right (45 to 90)
            elif angle >= math.pi / 4 and angle < math.pi / 2:
                label_x = x + 2
                label_y = y - 1
            # Top (90 to 135)
            elif angle >= math.pi / 2 and angle < 3 * math.pi / 4:
                label_x = x - len(label) // 2
                label_y = y - 1
            # Top left (135 to 180)
            elif angle >= 3 * math.pi / 4 and angle < math.pi:
                label_x = x - len(label) - 1
                label_y = y - 1
            # Left (180 to 225)
            elif angle >= math.pi and angle < 5 * math.pi / 4:
                label_x = x - len(label) - 1
                label_y = y
            # Bottom left (225 to 270)
            elif angle >= 5 * math.pi / 4 and angle < 3 * math.pi / 2:
                label_x = x - len(label) - 1
                label_y = y + 1
            # Bottom (270 to 315)
            elif angle >= 3 * math.pi / 2 and angle < 7 * math.pi / 4:
                label_x = x - len(label) // 2
                label_y = y + 1
            else:
                label_x = x + 2
                label_y = y

            # Draw label character by character
            for j, char in enumerate(label):
                lx = label_x + j
                ly = label_y
                if 0 <= ly < height and 0 <= lx < width:
                    if canvas[ly][lx] == ' ':  # Only draw if space is empty
                        canvas[ly][lx] = char

    # Render canvas with rich formatting
    console.print()
    for row in canvas:
        line = ''.join(row)
        console.print(line)

    console.print()
    console.print(Panel(
        "[bold cyan]Legend:[/]\n"
        "👤 = Profile  •  🏢 = Company  •  ─ = Relationship  •  ═ = Bidirectional  •  · = Works at",
        border_style="cyan",
        box=box.SIMPLE
    ))
    console.print()

    # Show node labels below the map
    console.print("[bold cyan]Nodes:[/]")

    # Group by type
    profile_nodes = [n for n in nodes if n['type'] == 'profile']
    company_nodes = [n for n in nodes if n['type'] == 'company']

    if profile_nodes:
        console.print("\n[bold yellow]👤 Profiles:[/]")
        for node in profile_nodes[:10]:  # Show first 10
            console.print(f"  • {node['name']}")
        if len(profile_nodes) > 10:
            console.print(f"  [dim]... and {len(profile_nodes) - 10} more[/]")

    if company_nodes:
        console.print("\n[bold yellow]🏢 Companies:[/]")
        for node in company_nodes[:10]:
            console.print(f"  • {node['name']}")
        if len(company_nodes) > 10:
            console.print(f"  [dim]... and {len(company_nodes) - 10} more[/]")

    # Show statistics
    console.print()
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan bold", justify="right")
    stats_table.add_column(style="white")

    stats_table.add_row("Total Nodes:", str(len(nodes)))
    stats_table.add_row("Profiles:", str(len(profile_nodes)))
    stats_table.add_row("Companies:", str(len(company_nodes)))
    stats_table.add_row("Relationships:", str(len(profile_relationships)))
    stats_table.add_row("Company Relations:", str(len(company_relationships)))
    stats_table.add_row("Total Connections:", str(len(edges)))

    console.print(Panel(stats_table, title="[bold cyan]Network Stats[/]", border_style="cyan"))

    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()
    session.close()


def browse_profiles():
    """Browse and manage profiles interactively"""
    session = get_session()

    while True:
        console.clear()
        profiles = session.query(Profile).order_by(Profile.name).all()

        if not profiles:
            console.print("\n[yellow]No profiles found.[/]\n")
            console.print("Press Enter to go back or 'a' to add a profile")
            action = questionary.text("", style=custom_style).ask()
            if action and action.lower() == 'a':
                add_profile_interactive()
            else:
                break
            continue

        # Create choices with profile info
        choices = []
        for p in profiles:
            company = f"@ {p.company.name}" if p.company else ""
            tags = f"[{', '.join([t.name for t in p.tags[:2]])}]" if p.tags else ""
            choice_text = f"{p.name:<25} {p.seniority:<12} {company:<20} {tags}"
            choices.append({
                'name': choice_text,
                'value': p.id
            })

        choices.append({'name': '← Back to Main Menu', 'value': 'back'})

        console.print(Panel(
            f"[bold cyan]Profiles ({len(profiles)} total)[/]\n"
            "[dim]Select a profile to view details[/]",
            border_style="cyan"
        ))
        console.print()

        selected = questionary.select(
            "Select profile:",
            choices=choices,
            style=custom_style
        ).ask()

        if not selected or selected == 'back':
            break

        # Show profile details
        show_profile_details(selected, session)

    session.close()


def show_profile_details(profile_id, session):
    """Show detailed view of a profile with actions"""
    profile = session.query(Profile).filter(Profile.id == profile_id).first()

    if not profile:
        console.print("[red]Profile not found[/]")
        return

    while True:
        console.clear()

        # Display profile info
        table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        table.add_column("Field", style="cyan bold", width=20)
        table.add_column("Value", style="white")

        table.add_row("Name", profile.name)
        table.add_row("Email", profile.email or "-")
        table.add_row("Phone", profile.phone or "-")
        table.add_row("Seniority", profile.seniority)
        table.add_row("Company", profile.company.name if profile.company else "-")
        table.add_row("Generation", profile.generation or "-")
        table.add_row("Married", "Yes" if profile.married else "No")
        table.add_row("Has Children", "Yes" if profile.has_children else "No")

        if profile.good_at:
            table.add_row("Skills", profile.good_at)

        if profile.tags:
            table.add_row("Tags", ", ".join([t.name for t in profile.tags]))

        if profile.notes:
            table.add_row("Notes", profile.notes[:50] + "..." if len(profile.notes) > 50 else profile.notes)

        console.print(Panel(table, title=f"[bold cyan]Profile Details[/]", border_style="cyan"))
        console.print()

        # Action menu
        actions = [
            "📝 Edit Profile",
            "🗑️  Delete Profile",
            "← Back to List"
        ]

        action = questionary.select(
            "What would you like to do?",
            choices=actions,
            style=custom_style
        ).ask()

        if not action or action == "← Back to List":
            break

        elif action == "📝 Edit Profile":
            edit_profile_interactive(profile, session)

        elif action == "🗑️  Delete Profile":
            if questionary.confirm(f"Are you sure you want to delete {profile.name}?", style=custom_style).ask():
                session.delete(profile)
                session.commit()
                console.print(f"\n[green]✓ Deleted {profile.name}[/]\n")
                questionary.press_any_key_to_continue().ask()
                break


def add_profile_interactive():
    """Add a new profile with interactive form"""
    console.clear()
    console.print(Panel(
        "[bold cyan]Add New Profile[/]\n"
        "[dim]Fill in the profile information[/]",
        border_style="cyan"
    ))
    console.print()

    # Collect information
    name = questionary.text("Name:", style=custom_style, validate=lambda x: len(x) > 0).ask()
    if not name:
        return

    seniority = questionary.select(
        "Seniority:",
        choices=[s.title() for s in SENIORITY_LEVELS],
        style=custom_style
    ).ask()

    email = questionary.text(
        "Email (optional):",
        style=custom_style,
        validate=lambda x: len(x) == 0 or validate_email(x)
    ).ask()

    phone = questionary.text("Phone (optional):", style=custom_style).ask()

    # Company selection
    session = get_session()
    companies = session.query(Company).order_by(Company.name).all()

    if companies:
        company_choices = [{'name': c.name, 'value': c.id} for c in companies]
        company_choices.insert(0, {'name': '-- No Company --', 'value': None})
        company_choices.append({'name': '+ Create New Company', 'value': 'new'})

        company_id = questionary.select(
            "Company:",
            choices=company_choices,
            style=custom_style
        ).ask()

        if company_id == 'new':
            company_name = questionary.text("New company name:", style=custom_style).ask()
            if company_name:
                new_company = Company(name=company_name)
                session.add(new_company)
                session.flush()
                company_id = new_company.id
        elif company_id is None:
            company_id = None
    else:
        create_company = questionary.confirm("No companies found. Create one?", style=custom_style).ask()
        if create_company:
            company_name = questionary.text("Company name:", style=custom_style).ask()
            if company_name:
                new_company = Company(name=company_name)
                session.add(new_company)
                session.flush()
                company_id = new_company.id
        else:
            company_id = None

    # Tags
    tags_input = questionary.text(
        "Tags (comma-separated, optional):",
        style=custom_style
    ).ask()

    # Additional info
    add_more = questionary.confirm("Add more details?", style=custom_style, default=False).ask()

    generation = None
    married = False
    has_children = False
    skills = None
    notes = None

    if add_more:
        generation = questionary.select(
            "Generation (optional):",
            choices=['Skip'] + [g.title() for g in GENERATION_TYPES],
            style=custom_style
        ).ask()
        if generation == 'Skip':
            generation = None

        married = questionary.confirm("Married?", style=custom_style, default=False).ask()
        has_children = questionary.confirm("Has children?", style=custom_style, default=False).ask()
        skills = questionary.text("Skills (optional):", style=custom_style).ask()
        notes = questionary.text("Notes (optional):", style=custom_style).ask()

    # Create profile
    try:
        new_profile = Profile(
            name=name,
            seniority=seniority.lower(),
            email=email or None,
            phone=phone or None,
            company_id=company_id,
            generation=generation.lower() if generation else None,
            married=married,
            has_children=has_children,
            good_at=skills or None,
            notes=notes or None
        )

        session.add(new_profile)
        session.flush()

        # Handle tags
        if tags_input:
            tag_names = parse_tags(tags_input)
            for tag_name in tag_names:
                tag = session.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                new_profile.tags.append(tag)

        session.commit()

        console.print(f"\n[green]✓ Profile '{name}' created successfully![/]\n")
        questionary.press_any_key_to_continue().ask()

    except Exception as e:
        console.print(f"\n[red]✗ Error creating profile: {str(e)}[/]\n")
        session.rollback()
        questionary.press_any_key_to_continue().ask()
    finally:
        session.close()


def edit_profile_interactive(profile, session):
    """Edit profile interactively - allows editing multiple fields"""

    while True:
        console.clear()
        console.print(Panel(
            f"[bold cyan]Edit Profile: {profile.name}[/]",
            border_style="cyan"
        ))
        console.print()

        # Show current values
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column(style="dim", justify="right")
        info_table.add_column(style="white")

        info_table.add_row("Name:", profile.name)
        info_table.add_row("Email:", profile.email or "-")
        info_table.add_row("Phone:", profile.phone or "-")
        info_table.add_row("Seniority:", profile.seniority.title())
        info_table.add_row("Company:", profile.company.name if profile.company else "-")
        info_table.add_row("Tags:", ", ".join([t.name for t in profile.tags]) if profile.tags else "-")
        info_table.add_row("Skills:", profile.good_at or "-")

        console.print(info_table)
        console.print()

        # What to edit
        fields = [
            "Name",
            "Email",
            "Phone",
            "Seniority",
            "Company",
            "Tags",
            "Skills",
            "Notes",
            "← Done Editing"
        ]

        field = questionary.select(
            "What would you like to edit?",
            choices=fields,
            style=custom_style
        ).ask()

        if not field or field == "← Done Editing":
            break

        if field == "Name":
            new_value = questionary.text("Name:", default=profile.name, style=custom_style).ask()
            if new_value:
                profile.name = new_value

        elif field == "Email":
            new_value = questionary.text("Email:", default=profile.email or "", style=custom_style).ask()
            profile.email = new_value or None

        elif field == "Phone":
            new_value = questionary.text("Phone:", default=profile.phone or "", style=custom_style).ask()
            profile.phone = new_value or None

        elif field == "Seniority":
            new_value = questionary.select(
                "Seniority:",
                choices=[s.title() for s in SENIORITY_LEVELS],
                default=profile.seniority.title(),
                style=custom_style
            ).ask()
            if new_value:
                profile.seniority = new_value.lower()

        elif field == "Company":
            companies = session.query(Company).order_by(Company.name).all()
            company_choices = [{'name': '-- No Company --', 'value': None}]
            company_choices.extend([{'name': c.name, 'value': c.id} for c in companies])
            company_choices.append({'name': '+ Create New', 'value': 'new'})

            company_id = questionary.select(
                "Company:",
                choices=company_choices,
                style=custom_style
            ).ask()

            if company_id == 'new':
                company_name = questionary.text("New company name:", style=custom_style).ask()
                if company_name:
                    new_company = Company(name=company_name)
                    session.add(new_company)
                    session.flush()
                    profile.company_id = new_company.id
            else:
                profile.company_id = company_id

        elif field == "Tags":
            current_tags = ", ".join([t.name for t in profile.tags])
            new_value = questionary.text("Tags (comma-separated):", default=current_tags, style=custom_style).ask()
            if new_value is not None:
                # Clear existing tags
                profile.tags = []
                # Add new tags
                tag_names = parse_tags(new_value)
                for tag_name in tag_names:
                    tag = session.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                        session.flush()
                    profile.tags.append(tag)

        elif field == "Skills":
            new_value = questionary.text("Skills:", default=profile.good_at or "", style=custom_style).ask()
            profile.good_at = new_value or None

        elif field == "Notes":
            new_value = questionary.text("Notes:", default=profile.notes or "", style=custom_style).ask()
            profile.notes = new_value or None

        # Commit after each field change
        session.commit()
        console.print(f"\n[green]✓ Updated {profile.name}[/]\n")
        import time
        time.sleep(0.5)  # Brief pause to show success message


def browse_companies():
    """Browse companies interactively"""
    session = get_session()

    while True:
        console.clear()
        companies = session.query(Company).order_by(Company.name).all()

        if not companies:
            console.print("\n[yellow]No companies found.[/]\n")
            questionary.press_any_key_to_continue().ask()
            break

        # Create table
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Industry", style="blue")
        table.add_column("Profiles", justify="right", style="green")

        for c in companies:
            table.add_row(
                c.name,
                c.industry or "-",
                str(len(c.profiles))
            )

        console.print(Panel(table, title=f"[bold cyan]Companies ({len(companies)} total)[/]", border_style="cyan"))
        console.print()

        questionary.press_any_key_to_continue("Press any key to go back...").ask()
        break

    session.close()


def show_company_details(company, session):
    """Show detailed view of a company with its profiles"""
    console.clear()

    # Display company info
    table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
    table.add_column("Field", style="cyan bold", width=20)
    table.add_column("Value", style="white")

    table.add_row("Name", company.name)
    table.add_row("Industry", company.industry or "-")
    table.add_row("Size", company.size or "-")
    table.add_row("Location", company.location or "-")
    table.add_row("Website", company.website or "-")
    if company.notes:
        table.add_row("Notes", company.notes[:100] + "..." if len(company.notes) > 100 else company.notes)

    console.print(Panel(table, title=f"[bold cyan]Company Details[/]", border_style="cyan"))
    console.print()

    # Show profiles at this company
    if company.profiles:
        console.print(f"[bold yellow]Profiles at {company.name}:[/]\n")
        profiles_table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="yellow")
        profiles_table.add_column("Name", style="cyan")
        profiles_table.add_column("Seniority", style="blue")
        profiles_table.add_column("Email", style="green")

        for p in company.profiles[:10]:  # Show first 10
            profiles_table.add_row(
                p.name,
                p.seniority.title(),
                p.email or "-"
            )

        console.print(profiles_table)
        if len(company.profiles) > 10:
            console.print(f"\n[dim]... and {len(company.profiles) - 10} more[/]")
    else:
        console.print("[dim]No profiles associated with this company yet[/]")

    console.print()
    questionary.press_any_key_to_continue("Press any key to go back...").ask()


def add_company_interactive():
    """Add a new company interactively"""
    console.clear()
    console.print(Panel(
        "[bold cyan]Add New Company[/]",
        border_style="cyan"
    ))
    console.print()

    name = questionary.text("Company name:", style=custom_style).ask()
    if not name:
        return

    industry = questionary.text("Industry (optional):", style=custom_style).ask()
    size = questionary.text("Size (optional):", style=custom_style).ask()
    location = questionary.text("Location (optional):", style=custom_style).ask()
    website = questionary.text("Website (optional):", style=custom_style).ask()

    session = get_session()
    try:
        new_company = Company(
            name=name,
            industry=industry or None,
            size=size or None,
            location=location or None,
            website=website or None
        )

        session.add(new_company)
        session.commit()

        console.print(f"\n[green]✓ Company '{name}' created successfully![/]\n")
        questionary.press_any_key_to_continue().ask()

    except Exception as e:
        console.print(f"\n[red]✗ Error creating company: {str(e)}[/]\n")
        session.rollback()
        questionary.press_any_key_to_continue().ask()
    finally:
        session.close()


def search_interactive():
    """Interactive search"""
    console.clear()
    console.print(Panel(
        "[bold cyan]Search Profiles[/]",
        border_style="cyan"
    ))
    console.print()

    query = questionary.text("Search:", style=custom_style).ask()
    if not query:
        return

    session = get_session()
    from sqlalchemy import or_

    results = session.query(Profile).filter(
        or_(
            Profile.name.ilike(f"%{query}%"),
            Profile.email.ilike(f"%{query}%"),
            Profile.good_at.ilike(f"%{query}%")
        )
    ).all()

    console.print()
    if results:
        console.print(f"[green]Found {len(results)} results:[/]\n")
        for p in results:
            company = f"@ {p.company.name}" if p.company else ""
            console.print(f"  • [cyan]{p.name}[/] ({p.seniority}) {company}")
    else:
        console.print("[yellow]No results found[/]")

    console.print()
    questionary.press_any_key_to_continue().ask()
    session.close()


def manage_tags():
    """Manage tags interactively (legacy function)"""
    view_tags_detailed()


def edit_company_menu():
    """Edit company selection menu"""
    session = get_session()
    companies = session.query(Company).order_by(Company.name).all()

    if not companies:
        console.print("\n[yellow]No companies found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Create choices
    company_choices = [{'name': c.name, 'value': c.id} for c in companies]
    company_choices.append({'name': '← Cancel', 'value': None})

    console.clear()
    console.print(Panel(
        "[bold cyan]✏️  Edit Company[/]\n"
        "[dim]Select a company to edit[/]",
        border_style="cyan"
    ))
    console.print()

    company_id = questionary.select(
        "Select company:",
        choices=company_choices,
        style=custom_style
    ).ask()

    if company_id:
        company = session.query(Company).filter(Company.id == company_id).first()
        if company:
            edit_company_interactive(company, session)

    session.close()


def edit_company_interactive(company, session):
    """Edit a company interactively - allows editing multiple fields"""

    while True:
        console.clear()
        console.print(Panel(
            f"[bold cyan]Edit Company: {company.name}[/]",
            border_style="cyan"
        ))
        console.print()

        # Show current values
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column(style="dim", justify="right")
        info_table.add_column(style="white")

        info_table.add_row("Name:", company.name)
        info_table.add_row("Industry:", company.industry or "-")
        info_table.add_row("Size:", company.size or "-")
        info_table.add_row("Location:", company.location or "-")
        info_table.add_row("Website:", company.website or "-")
        info_table.add_row("Profiles:", str(len(company.profiles)))

        console.print(info_table)
        console.print()

        fields = [
            "Name",
            "Industry",
            "Size",
            "Location",
            "Website",
            "Notes",
            "← Done Editing"
        ]

        field = questionary.select(
            "What would you like to edit?",
            choices=fields,
            style=custom_style
        ).ask()

        if not field or field == "← Done Editing":
            break

        if field == "Name":
            new_value = questionary.text("Company name:", default=company.name, style=custom_style).ask()
            if new_value:
                company.name = new_value
        elif field == "Industry":
            new_value = questionary.text("Industry:", default=company.industry or "", style=custom_style).ask()
            company.industry = new_value or None
        elif field == "Size":
            new_value = questionary.text("Size:", default=company.size or "", style=custom_style).ask()
            company.size = new_value or None
        elif field == "Location":
            new_value = questionary.text("Location:", default=company.location or "", style=custom_style).ask()
            company.location = new_value or None
        elif field == "Website":
            new_value = questionary.text("Website:", default=company.website or "", style=custom_style).ask()
            company.website = new_value or None
        elif field == "Notes":
            new_value = questionary.text("Notes:", default=company.notes or "", style=custom_style).ask()
            company.notes = new_value or None

        # Commit after each field change
        session.commit()
        console.print(f"\n[green]✓ Updated {company.name}[/]\n")
        import time
        time.sleep(0.5)  # Brief pause to show success message


def view_tags_detailed():
    """View all tags with detailed information"""
    session = get_session()
    tags = session.query(Tag).order_by(Tag.name).all()

    console.clear()
    console.print(Panel(
        f"[bold cyan]Tags ({len(tags)} total)[/]",
        border_style="cyan"
    ))
    console.print()

    if tags:
        # Create table
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
        table.add_column("Tag", style="cyan")
        table.add_column("Color", style="white")
        table.add_column("Profiles", justify="right", style="green")

        for tag in tags:
            count = len(tag.profiles)
            color_display = f"[{tag.color or 'white'}]●[/]" if tag.color else "-"
            table.add_row(tag.name, color_display, str(count))

        console.print(table)
    else:
        console.print("[yellow]No tags found[/]")

    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()
    session.close()


def add_tag_interactive():
    """Add a new tag interactively"""
    console.clear()
    console.print(Panel(
        "[bold cyan]➕ Add New Tag[/]",
        border_style="cyan"
    ))
    console.print()

    name = questionary.text("Tag name:", style=custom_style).ask()
    if not name:
        return

    color_choices = [
        "red", "green", "blue", "yellow", "cyan", "magenta",
        "white", "bright_red", "bright_green", "bright_blue"
    ]
    color = questionary.select("Color (optional):", choices=["Skip"] + color_choices, style=custom_style).ask()
    if color == "Skip":
        color = None

    session = get_session()
    try:
        # Check if tag already exists
        existing = session.query(Tag).filter(Tag.name == name).first()
        if existing:
            console.print(f"\n[yellow]Tag '{name}' already exists![/]\n")
            questionary.press_any_key_to_continue().ask()
            session.close()
            return

        new_tag = Tag(name=name, color=color)
        session.add(new_tag)
        session.commit()

        console.print(f"\n[green]✓ Tag '{name}' created successfully![/]\n")
        questionary.press_any_key_to_continue().ask()

    except Exception as e:
        console.print(f"\n[red]✗ Error creating tag: {str(e)}[/]\n")
        session.rollback()
        questionary.press_any_key_to_continue().ask()
    finally:
        session.close()


def edit_tag_interactive():
    """Edit a tag interactively"""
    session = get_session()
    tags = session.query(Tag).order_by(Tag.name).all()

    if not tags:
        console.print("\n[yellow]No tags found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Create choices
    tag_choices = [{'name': t.name, 'value': t.id} for t in tags]
    tag_choices.append({'name': '← Cancel', 'value': None})

    console.clear()
    console.print(Panel(
        "[bold cyan]✏️  Edit Tag[/]\n"
        "[dim]Select a tag to edit[/]",
        border_style="cyan"
    ))
    console.print()

    tag_id = questionary.select(
        "Select tag:",
        choices=tag_choices,
        style=custom_style
    ).ask()

    if not tag_id:
        session.close()
        return

    tag = session.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        session.close()
        return

    # Edit options
    fields = ["Name", "Color", "← Cancel"]
    field = questionary.select(
        f"Edit {tag.name}:",
        choices=fields,
        style=custom_style
    ).ask()

    if not field or field == "← Cancel":
        session.close()
        return

    if field == "Name":
        new_name = questionary.text("Tag name:", default=tag.name, style=custom_style).ask()
        if new_name:
            tag.name = new_name
    elif field == "Color":
        color_choices = [
            "red", "green", "blue", "yellow", "cyan", "magenta",
            "white", "bright_red", "bright_green", "bright_blue"
        ]
        new_color = questionary.select(
            "Color:",
            choices=["None"] + color_choices,
            default=tag.color or "None",
            style=custom_style
        ).ask()
        tag.color = None if new_color == "None" else new_color

    session.commit()
    console.print(f"\n[green]✓ Updated tag '{tag.name}'[/]\n")
    questionary.press_any_key_to_continue().ask()
    session.close()


def delete_tag_interactive():
    """Delete a tag interactively"""
    session = get_session()
    tags = session.query(Tag).order_by(Tag.name).all()

    if not tags:
        console.print("\n[yellow]No tags found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Create choices
    tag_choices = []
    for t in tags:
        count = len(t.profiles)
        tag_choices.append({'name': f"{t.name} ({count} profiles)", 'value': t.id})
    tag_choices.append({'name': '← Cancel', 'value': None})

    console.clear()
    console.print(Panel(
        "[bold cyan]🗑️  Delete Tag[/]\n"
        "[dim]Select a tag to delete[/]",
        border_style="cyan"
    ))
    console.print()

    tag_id = questionary.select(
        "Select tag:",
        choices=tag_choices,
        style=custom_style
    ).ask()

    if not tag_id:
        session.close()
        return

    tag = session.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        session.close()
        return

    # Confirm deletion
    profile_count = len(tag.profiles)
    if questionary.confirm(
        f"Delete tag '{tag.name}'? (Used by {profile_count} profile(s))",
        style=custom_style,
        default=False
    ).ask():
        session.delete(tag)
        session.commit()
        console.print(f"\n[green]✓ Deleted tag '{tag.name}'[/]\n")
        questionary.press_any_key_to_continue().ask()

    session.close()


def add_profile_relationship():
    """Add a relationship between two profiles"""
    from leadsauce.models.relationship import ProfileRelationship, PROFILE_RELATIONSHIP_TYPES, RELATIONSHIP_STATUS

    session = get_session()
    profiles = session.query(Profile).order_by(Profile.name).all()

    if len(profiles) < 2:
        console.print("\n[yellow]You need at least 2 profiles to create a relationship.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold cyan]➕ Add Profile Relationship[/]\n"
        "[dim]Create a connection between two people[/]",
        border_style="cyan"
    ))
    console.print()

    # Select FROM profile
    from_choices = [{'name': f"{p.name} ({p.company.name if p.company else 'No company'})", 'value': p.id} for p in profiles]
    from_choices.append({'name': '← Cancel', 'value': None})

    from_profile_id = questionary.select(
        "From (source person):",
        choices=from_choices,
        style=custom_style
    ).ask()

    if not from_profile_id:
        session.close()
        return

    # Select TO profile (exclude the FROM profile)
    to_choices = [{'name': f"{p.name} ({p.company.name if p.company else 'No company'})", 'value': p.id} 
                  for p in profiles if p.id != from_profile_id]
    to_choices.append({'name': '← Cancel', 'value': None})

    to_profile_id = questionary.select(
        "To (target person):",
        choices=to_choices,
        style=custom_style
    ).ask()

    if not to_profile_id:
        session.close()
        return

    # Select relationship type
    relationship_type = questionary.select(
        "Relationship type:",
        choices=PROFILE_RELATIONSHIP_TYPES,
        style=custom_style
    ).ask()

    # Is it bidirectional?
    bidirectional = questionary.confirm(
        "Is this a two-way relationship? (e.g., 'friends' vs 'reports to')",
        style=custom_style,
        default=True
    ).ask()

    # Select status
    status = questionary.select(
        "Relationship status:",
        choices=RELATIONSHIP_STATUS,
        style=custom_style,
        default="Good"
    ).ask()

    # Optional description
    description = questionary.text(
        "Description (optional):",
        style=custom_style
    ).ask()

    # Create relationship
    try:
        new_relationship = ProfileRelationship(
            from_profile_id=from_profile_id,
            to_profile_id=to_profile_id,
            relationship_type=relationship_type,
            status=status,
            bidirectional=bidirectional,
            description=description or None
        )

        session.add(new_relationship)
        session.commit()

        from_profile = session.query(Profile).filter(Profile.id == from_profile_id).first()
        to_profile = session.query(Profile).filter(Profile.id == to_profile_id).first()

        console.print(f"\n[green]✓ Created relationship: {from_profile.name} → {relationship_type} → {to_profile.name}[/]\n")
        if bidirectional:
            console.print(f"[dim](Bidirectional relationship created)[/]\n")
        questionary.press_any_key_to_continue().ask()

    except Exception as e:
        console.print(f"\n[red]✗ Error creating relationship: {str(e)}[/]\n")
        session.rollback()
        questionary.press_any_key_to_continue().ask()
    finally:
        session.close()


def view_profile_relationships():
    """View all profile relationships"""
    from leadsauce.models.relationship import ProfileRelationship

    session = get_session()
    relationships = session.query(ProfileRelationship).all()

    console.clear()
    console.print(Panel(
        f"[bold cyan]Profile Relationships ({len(relationships)} total)[/]",
        border_style="cyan"
    ))
    console.print()

    if relationships:
        # Group by from_profile
        by_profile = {}
        for rel in relationships:
            if rel.from_profile_id not in by_profile:
                by_profile[rel.from_profile_id] = []
            by_profile[rel.from_profile_id].append(rel)

        for profile_id, rels in by_profile.items():
            profile = rels[0].from_profile
            console.print(f"[cyan]{profile.name}[/]")

            for rel in rels:
                arrow = "↔" if rel.bidirectional else "→"
                # Color code status
                status_color = "green" if rel.status == "Good" else "red" if rel.status == "Bad" else "dim"
                console.print(f"  {arrow} [yellow]{rel.relationship_type}[/] → [white]{rel.to_profile.name}[/] [{status_color}][{rel.status}][/]")
                if rel.description:
                    console.print(f"     [dim]{rel.description}[/]")

            console.print()
    else:
        console.print("[yellow]No relationships created yet.[/]")

    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()
    session.close()


def add_company_relationship():
    """Add a relationship between two companies"""
    from leadsauce.models.relationship import CompanyRelationship, COMPANY_RELATIONSHIP_TYPES, RELATIONSHIP_STATUS

    session = get_session()
    companies = session.query(Company).order_by(Company.name).all()

    if len(companies) < 2:
        console.print("\n[yellow]You need at least 2 companies to create a relationship.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold cyan]➕ Add Company Relationship[/]\n"
        "[dim]Create a connection between two companies[/]",
        border_style="cyan"
    ))
    console.print()

    # Select FROM company
    from_choices = [{'name': f"{c.name} ({c.industry or 'No industry'})", 'value': c.id} for c in companies]
    from_choices.append({'name': '← Cancel', 'value': None})

    from_company_id = questionary.select(
        "From (source company):",
        choices=from_choices,
        style=custom_style
    ).ask()

    if not from_company_id:
        session.close()
        return

    # Select TO company (exclude the FROM company)
    to_choices = [{'name': f"{c.name} ({c.industry or 'No industry'})", 'value': c.id} 
                  for c in companies if c.id != from_company_id]
    to_choices.append({'name': '← Cancel', 'value': None})

    to_company_id = questionary.select(
        "To (target company):",
        choices=to_choices,
        style=custom_style
    ).ask()

    if not to_company_id:
        session.close()
        return

    # Select relationship type
    relationship_type = questionary.select(
        "Relationship type:",
        choices=COMPANY_RELATIONSHIP_TYPES,
        style=custom_style
    ).ask()

    # Is it bidirectional?
    bidirectional = questionary.confirm(
        "Is this a two-way relationship? (e.g., 'partners' vs 'supplier')",
        style=custom_style,
        default=True
    ).ask()

    # Select status
    status = questionary.select(
        "Relationship status:",
        choices=RELATIONSHIP_STATUS,
        style=custom_style,
        default="Good"
    ).ask()

    # Optional description
    description = questionary.text(
        "Description (optional):",
        style=custom_style
    ).ask()

    # Create relationship
    try:
        new_relationship = CompanyRelationship(
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            relationship_type=relationship_type,
            status=status,
            bidirectional=bidirectional,
            description=description or None
        )

        session.add(new_relationship)
        session.commit()

        from_company = session.query(Company).filter(Company.id == from_company_id).first()
        to_company = session.query(Company).filter(Company.id == to_company_id).first()

        console.print(f"\n[green]✓ Created relationship: {from_company.name} → {relationship_type} → {to_company.name}[/]\n")
        if bidirectional:
            console.print(f"[dim](Bidirectional relationship created)[/]\n")
        questionary.press_any_key_to_continue().ask()

    except Exception as e:
        console.print(f"\n[red]✗ Error creating relationship: {str(e)}[/]\n")
        session.rollback()
        questionary.press_any_key_to_continue().ask()
    finally:
        session.close()


def view_company_relationships():
    """View all company relationships"""
    from leadsauce.models.relationship import CompanyRelationship

    session = get_session()
    relationships = session.query(CompanyRelationship).all()

    console.clear()
    console.print(Panel(
        f"[bold cyan]Company Relationships ({len(relationships)} total)[/]",
        border_style="cyan"
    ))
    console.print()

    if relationships:
        # Group by from_company
        by_company = {}
        for rel in relationships:
            if rel.from_company_id not in by_company:
                by_company[rel.from_company_id] = []
            by_company[rel.from_company_id].append(rel)

        for company_id, rels in by_company.items():
            company = rels[0].from_company
            console.print(f"[cyan]{company.name}[/]")

            for rel in rels:
                arrow = "↔" if rel.bidirectional else "→"
                # Color code status
                status_color = "green" if rel.status == "Good" else "red" if rel.status == "Bad" else "dim"
                console.print(f"  {arrow} [yellow]{rel.relationship_type}[/] → [white]{rel.to_company.name}[/] [{status_color}][{rel.status}][/]")
                if rel.description:
                    console.print(f"     [dim]{rel.description}[/]")

            console.print()
    else:
        console.print("[yellow]No relationships created yet.[/]")

    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()
    session.close()


def edit_profile_relationship():
    """Edit an existing profile relationship"""
    from leadsauce.models.relationship import ProfileRelationship, PROFILE_RELATIONSHIP_TYPES, RELATIONSHIP_STATUS

    session = get_session()
    relationships = session.query(ProfileRelationship).all()

    if not relationships:
        console.print("\n[yellow]No profile relationships to edit.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold cyan]✏️  Edit Profile Relationship[/]\n"
        "[dim]Select a relationship to edit[/]",
        border_style="cyan"
    ))
    console.print()

    # Build choices
    rel_choices = []
    for rel in relationships:
        arrow = "↔" if rel.bidirectional else "→"
        status_label = f"[{rel.status}]"
        label = f"{rel.from_profile.name} {arrow} {rel.relationship_type} → {rel.to_profile.name} {status_label}"
        rel_choices.append({'name': label, 'value': rel.id})
    rel_choices.append({'name': '← Cancel', 'value': None})

    rel_id = questionary.select(
        "Select relationship to edit:",
        choices=rel_choices,
        style=custom_style
    ).ask()

    if not rel_id:
        session.close()
        return

    # Get the relationship
    relationship = session.query(ProfileRelationship).filter(ProfileRelationship.id == rel_id).first()

    if not relationship:
        console.print("\n[red]Relationship not found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Edit loop
    while True:
        console.clear()
        console.print(Panel(
            f"[bold cyan]Editing Relationship[/]\n"
            f"[white]{relationship.from_profile.name}[/] → [white]{relationship.to_profile.name}[/]",
            border_style="cyan"
        ))
        console.print()

        # Show current values
        arrow = "↔" if relationship.bidirectional else "→"
        status_color = "green" if relationship.status == "Good" else "red" if relationship.status == "Bad" else "dim"

        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column(style="cyan bold", justify="right")
        info_table.add_column(style="white")

        info_table.add_row("Type:", relationship.relationship_type)
        info_table.add_row("Status:", f"[{status_color}]{relationship.status}[/]")
        info_table.add_row("Bidirectional:", f"{arrow} {'Yes' if relationship.bidirectional else 'No'}")
        info_table.add_row("Description:", relationship.description or "-")

        console.print(info_table)
        console.print()

        # Edit options
        edit_choices = [
            "Relationship Type",
            "Status",
            "Bidirectional",
            "Description",
            "🗑️  Delete Relationship",
            "← Done Editing"
        ]

        field = questionary.select(
            "What would you like to edit?",
            choices=edit_choices,
            style=custom_style
        ).ask()

        if not field or field == "← Done Editing":
            break

        if field == "Relationship Type":
            new_type = questionary.select(
                "Relationship type:",
                choices=PROFILE_RELATIONSHIP_TYPES,
                style=custom_style,
                default=relationship.relationship_type if relationship.relationship_type in PROFILE_RELATIONSHIP_TYPES else None
            ).ask()
            if new_type:
                relationship.relationship_type = new_type
                session.commit()
                console.print(f"\n[green]✓ Updated relationship type to '{new_type}'[/]\n")
                time.sleep(0.5)

        elif field == "Status":
            new_status = questionary.select(
                "Relationship status:",
                choices=RELATIONSHIP_STATUS,
                style=custom_style,
                default=relationship.status if relationship.status in RELATIONSHIP_STATUS else "Good"
            ).ask()
            if new_status:
                relationship.status = new_status
                session.commit()
                console.print(f"\n[green]✓ Updated status to '{new_status}'[/]\n")
                time.sleep(0.5)

        elif field == "Bidirectional":
            new_bidirectional = questionary.confirm(
                "Is this a two-way relationship?",
                style=custom_style,
                default=relationship.bidirectional
            ).ask()
            relationship.bidirectional = new_bidirectional
            session.commit()
            console.print(f"\n[green]✓ Updated bidirectional to {'Yes' if new_bidirectional else 'No'}[/]\n")
            time.sleep(0.5)

        elif field == "Description":
            new_description = questionary.text(
                "Description (leave empty to clear):",
                style=custom_style,
                default=relationship.description or ""
            ).ask()
            relationship.description = new_description or None
            session.commit()
            console.print(f"\n[green]✓ Updated description[/]\n")
            time.sleep(0.5)

        elif field == "🗑️  Delete Relationship":
            confirm = questionary.confirm(
                f"Are you sure you want to delete this relationship?",
                style=custom_style,
                default=False
            ).ask()
            if confirm:
                session.delete(relationship)
                session.commit()
                console.print(f"\n[green]✓ Relationship deleted[/]\n")
                questionary.press_any_key_to_continue().ask()
                session.close()
                return

    session.close()


def edit_company_relationship():
    """Edit an existing company relationship"""
    from leadsauce.models.relationship import CompanyRelationship, COMPANY_RELATIONSHIP_TYPES, RELATIONSHIP_STATUS

    session = get_session()
    relationships = session.query(CompanyRelationship).all()

    if not relationships:
        console.print("\n[yellow]No company relationships to edit.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold cyan]✏️  Edit Company Relationship[/]\n"
        "[dim]Select a relationship to edit[/]",
        border_style="cyan"
    ))
    console.print()

    # Build choices
    rel_choices = []
    for rel in relationships:
        arrow = "↔" if rel.bidirectional else "→"
        status_label = f"[{rel.status}]"
        label = f"{rel.from_company.name} {arrow} {rel.relationship_type} → {rel.to_company.name} {status_label}"
        rel_choices.append({'name': label, 'value': rel.id})
    rel_choices.append({'name': '← Cancel', 'value': None})

    rel_id = questionary.select(
        "Select relationship to edit:",
        choices=rel_choices,
        style=custom_style
    ).ask()

    if not rel_id:
        session.close()
        return

    # Get the relationship
    relationship = session.query(CompanyRelationship).filter(CompanyRelationship.id == rel_id).first()

    if not relationship:
        console.print("\n[red]Relationship not found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Edit loop
    while True:
        console.clear()
        console.print(Panel(
            f"[bold cyan]Editing Relationship[/]\n"
            f"[white]{relationship.from_company.name}[/] → [white]{relationship.to_company.name}[/]",
            border_style="cyan"
        ))
        console.print()

        # Show current values
        arrow = "↔" if relationship.bidirectional else "→"
        status_color = "green" if relationship.status == "Good" else "red" if relationship.status == "Bad" else "dim"

        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column(style="cyan bold", justify="right")
        info_table.add_column(style="white")

        info_table.add_row("Type:", relationship.relationship_type)
        info_table.add_row("Status:", f"[{status_color}]{relationship.status}[/]")
        info_table.add_row("Bidirectional:", f"{arrow} {'Yes' if relationship.bidirectional else 'No'}")
        info_table.add_row("Description:", relationship.description or "-")

        console.print(info_table)
        console.print()

        # Edit options
        edit_choices = [
            "Relationship Type",
            "Status",
            "Bidirectional",
            "Description",
            "🗑️  Delete Relationship",
            "← Done Editing"
        ]

        field = questionary.select(
            "What would you like to edit?",
            choices=edit_choices,
            style=custom_style
        ).ask()

        if not field or field == "← Done Editing":
            break

        if field == "Relationship Type":
            new_type = questionary.select(
                "Relationship type:",
                choices=COMPANY_RELATIONSHIP_TYPES,
                style=custom_style,
                default=relationship.relationship_type if relationship.relationship_type in COMPANY_RELATIONSHIP_TYPES else None
            ).ask()
            if new_type:
                relationship.relationship_type = new_type
                session.commit()
                console.print(f"\n[green]✓ Updated relationship type to '{new_type}'[/]\n")
                time.sleep(0.5)

        elif field == "Status":
            new_status = questionary.select(
                "Relationship status:",
                choices=RELATIONSHIP_STATUS,
                style=custom_style,
                default=relationship.status if relationship.status in RELATIONSHIP_STATUS else "Good"
            ).ask()
            if new_status:
                relationship.status = new_status
                session.commit()
                console.print(f"\n[green]✓ Updated status to '{new_status}'[/]\n")
                time.sleep(0.5)

        elif field == "Bidirectional":
            new_bidirectional = questionary.confirm(
                "Is this a two-way relationship?",
                style=custom_style,
                default=relationship.bidirectional
            ).ask()
            relationship.bidirectional = new_bidirectional
            session.commit()
            console.print(f"\n[green]✓ Updated bidirectional to {'Yes' if new_bidirectional else 'No'}[/]\n")
            time.sleep(0.5)

        elif field == "Description":
            new_description = questionary.text(
                "Description (leave empty to clear):",
                style=custom_style,
                default=relationship.description or ""
            ).ask()
            relationship.description = new_description or None
            session.commit()
            console.print(f"\n[green]✓ Updated description[/]\n")
            time.sleep(0.5)

        elif field == "🗑️  Delete Relationship":
            confirm = questionary.confirm(
                f"Are you sure you want to delete this relationship?",
                style=custom_style,
                default=False
            ).ask()
            if confirm:
                session.delete(relationship)
                session.commit()
                console.print(f"\n[green]✓ Relationship deleted[/]\n")
                questionary.press_any_key_to_continue().ask()
                session.close()
                return

    session.close()

def delete_profile_relationship():
    """Delete a profile relationship"""
    from leadsauce.models.relationship import ProfileRelationship

    session = get_session()
    relationships = session.query(ProfileRelationship).all()

    if not relationships:
        console.print("\n[yellow]No profile relationships to delete.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold red]🗑️  Delete Profile Relationship[/]\n"
        "[dim]Select a relationship to delete[/]",
        border_style="red"
    ))
    console.print()

    # Build choices
    rel_choices = []
    for rel in relationships:
        arrow = "↔" if rel.bidirectional else "→"
        status_label = f"[{rel.status}]"
        label = f"{rel.from_profile.name} {arrow} {rel.relationship_type} → {rel.to_profile.name} {status_label}"
        rel_choices.append({'name': label, 'value': rel.id})
    rel_choices.append({'name': '← Cancel', 'value': None})

    rel_id = questionary.select(
        "Select relationship to delete:",
        choices=rel_choices,
        style=custom_style
    ).ask()

    if not rel_id:
        session.close()
        return

    # Get the relationship
    relationship = session.query(ProfileRelationship).filter(ProfileRelationship.id == rel_id).first()

    if not relationship:
        console.print("\n[red]Relationship not found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Confirm deletion
    confirm = questionary.confirm(
        f"Delete relationship: {relationship.from_profile.name} → {relationship.relationship_type} → {relationship.to_profile.name}?",
        style=custom_style,
        default=False
    ).ask()

    if confirm:
        session.delete(relationship)
        session.commit()
        console.print(f"\n[green]✓ Relationship deleted successfully[/]\n")
    else:
        console.print(f"\n[yellow]Deletion cancelled[/]\n")

    questionary.press_any_key_to_continue().ask()
    session.close()


def delete_company_relationship():
    """Delete a company relationship"""
    from leadsauce.models.relationship import CompanyRelationship

    session = get_session()
    relationships = session.query(CompanyRelationship).all()

    if not relationships:
        console.print("\n[yellow]No company relationships to delete.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    console.clear()
    console.print(Panel(
        "[bold red]🗑️  Delete Company Relationship[/]\n"
        "[dim]Select a relationship to delete[/]",
        border_style="red"
    ))
    console.print()

    # Build choices
    rel_choices = []
    for rel in relationships:
        arrow = "↔" if rel.bidirectional else "→"
        status_label = f"[{rel.status}]"
        label = f"{rel.from_company.name} {arrow} {rel.relationship_type} → {rel.to_company.name} {status_label}"
        rel_choices.append({'name': label, 'value': rel.id})
    rel_choices.append({'name': '← Cancel', 'value': None})

    rel_id = questionary.select(
        "Select relationship to delete:",
        choices=rel_choices,
        style=custom_style
    ).ask()

    if not rel_id:
        session.close()
        return

    # Get the relationship
    relationship = session.query(CompanyRelationship).filter(CompanyRelationship.id == rel_id).first()

    if not relationship:
        console.print("\n[red]Relationship not found.[/]\n")
        questionary.press_any_key_to_continue().ask()
        session.close()
        return

    # Confirm deletion
    confirm = questionary.confirm(
        f"Delete relationship: {relationship.from_company.name} → {relationship.relationship_type} → {relationship.to_company.name}?",
        style=custom_style,
        default=False
    ).ask()

    if confirm:
        session.delete(relationship)
        session.commit()
        console.print(f"\n[green]✓ Relationship deleted successfully[/]\n")
    else:
        console.print(f"\n[yellow]Deletion cancelled[/]\n")

    questionary.press_any_key_to_continue().ask()
    session.close()
