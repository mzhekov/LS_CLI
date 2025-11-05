"""
Interactive TUI for LeadSauce CLI with top bar navigation
"""

import time
import sys
import tty
import termios
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
from leadsauce.models.task import Task
from leadsauce.utils.constants import SENIORITY_LEVELS, GENERATION_TYPES
from leadsauce.utils.validators import validate_email, validate_phone, parse_tags
from datetime import datetime, timedelta

console = Console()


def get_single_key():
    """Capture a single keypress without requiring Enter"""
    try:
        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            # Set terminal to raw mode
            tty.setraw(fd)
            # Read single character
            ch = sys.stdin.read(1)
            return ch
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except:
        # Fallback to regular input if terminal manipulation fails
        return input()


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
    ("Network & Relationships", "🗺️", "4"),
    ("Search", "🔍", "5"),
    ("Tags", "🏷️", "6"),
    ("Workshop", "🔧", "7"),
    ("Export", "📤", "8"),
    ("Import", "📥", "9"),
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
            new_view = show_dashboard_view()
            # If dashboard returns a view (user pressed number key), navigate to it
            if new_view:
                current_view = new_view
                continue
        elif current_view == "Profiles":
            new_view = profiles_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"  # Return to dashboard after
            continue
        elif current_view == "Companies":
            new_view = companies_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Network & Relationships":
            new_view = network_and_relationships_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Search":
            new_view = search_interactive()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Tags":
            new_view = tags_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Workshop":
            new_view = workshop_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Export":
            new_view = export_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Import":
            new_view = import_menu()
            if new_view:
                current_view = new_view
            else:
                current_view = "Dashboard"
            continue
        elif current_view == "Exit":
            console.print("\n[cyan]Goodbye! 👋[/]\n")
            break

        # Navigation menu at bottom - allow both keyboard shortcuts and arrow key selection
        console.print()
        console.print("[dim]Navigation:[/]")
        console.print("[dim]  • Type a number (1-9) or 'q' to quit[/]")
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
            console.print(f"[yellow]Invalid option '{nav_input}'. Use 1-9 or q[/]")
            import time
            time.sleep(1.5)


def show_dashboard_view():
    """Show the main dashboard with statistics and task management actions"""
    session = get_session()

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Dashboard"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[t] Add Task", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[c] Complete Task", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit Task", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[d] Delete Task", style="red")
        actions_text.append(" • ", style="dim")
        actions_text.append("[v] View All Tasks", style="cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[r] Refresh", style="blue")

        console.print(Panel(
            actions_text,
            title="[bold yellow]📊 Dashboard[/]",
            border_style="yellow",
            box=box.SIMPLE
        ))
        console.print()

        # Get statistics
        total_profiles = session.query(Profile).count()
        total_companies = session.query(Company).count()
        total_tags = session.query(Tag).count()
        total_tasks = session.query(Task).count()
        pending_tasks = session.query(Task).filter(Task.status.in_(['pending', 'in_progress'])).count()

        # Get recent profiles
        recent_profiles = session.query(Profile).order_by(Profile.created_at.desc()).limit(5).all()

        # Create statistics panel
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column(style="cyan bold", justify="right")
        stats_table.add_column(style="white")

        stats_table.add_row("Profiles:", str(total_profiles))
        stats_table.add_row("Companies:", str(total_companies))
        stats_table.add_row("Tags:", str(total_tags))
        stats_table.add_row("Tasks:", f"{pending_tasks}/{total_tasks} pending")

        console.print(Panel(stats_table, title="[bold yellow]📊 Overview[/]", border_style="yellow"))
        console.print()

        # Pending/Overdue Tasks
        from sqlalchemy.orm import joinedload
        upcoming_tasks = session.query(Task).options(
            joinedload(Task.profiles),
            joinedload(Task.companies),
            joinedload(Task.tags)
        ).filter(
            Task.status.in_(['pending', 'in_progress'])
        ).order_by(Task.due_date.asc().nullsfirst()).limit(10).all()

        if upcoming_tasks:
            tasks_table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="yellow")
            tasks_table.add_column("#", style="dim", width=3)
            tasks_table.add_column("Task", style="cyan", no_wrap=False, width=25)
            tasks_table.add_column("Description", style="dim", no_wrap=False, width=20)
            tasks_table.add_column("Status", width=10)
            tasks_table.add_column("Priority", width=8)
            tasks_table.add_column("Due", width=12)
            tasks_table.add_column("Linked To", style="dim", no_wrap=False)

            for idx, task in enumerate(upcoming_tasks, 1):
                # Priority color
                priority_color = {
                    'low': 'blue',
                    'medium': 'yellow',
                    'high': 'magenta',
                    'urgent': 'red bold'
                }.get(task.priority, 'white')

                # Status color
                status_color = {
                    'pending': 'yellow',
                    'in_progress': 'cyan',
                    'completed': 'green',
                    'cancelled': 'red'
                }.get(task.status, 'white')

                # Due date formatting
                due_display = ""
                if task.due_date:
                    due_str = task.due_date.strftime('%Y-%m-%d')
                    if task.is_overdue():
                        due_display = f"[red bold]{due_str} ⚠️[/]"
                    elif task.due_date.date() == datetime.now().date():
                        due_display = f"[yellow bold]{due_str}[/]"
                    else:
                        due_display = due_str
                else:
                    due_display = "-"

                # Description (truncated)
                description = ""
                if task.description:
                    description = task.description[:20] + "..." if len(task.description) > 20 else task.description
                else:
                    description = "-"

                # Linked entities with names (show all: profiles, companies, and tags)
                linked_parts = []
                if task.profiles:
                    profile_names = [p.name for p in task.profiles[:2]]
                    if len(task.profiles) > 2:
                        profile_names.append(f"+{len(task.profiles)-2}")
                    linked_parts.append(f"👥 {', '.join(profile_names)}")
                if task.companies:
                    company_names = [c.name for c in task.companies[:2]]
                    if len(task.companies) > 2:
                        company_names.append(f"+{len(task.companies)-2}")
                    linked_parts.append(f"🏢 {', '.join(company_names)}")
                if task.tags:
                    tag_names = [t.name for t in task.tags[:2]]
                    if len(task.tags) > 2:
                        tag_names.append(f"+{len(task.tags)-2}")
                    linked_parts.append(f"🏷️ {', '.join(tag_names)}")

                linked_display = "\n".join(linked_parts) if linked_parts else "-"

                tasks_table.add_row(
                    str(idx),
                    task.title[:25] + "..." if len(task.title) > 25 else task.title,
                    description,
                    f"[{status_color}]{task.status.replace('_', ' ').title()}[/]",
                    f"[{priority_color}]{task.priority.upper()}[/]",
                    due_display,
                    linked_display
                )

            console.print(Panel(tasks_table, title="[bold yellow]📋 Upcoming Tasks[/]", border_style="yellow"))
        else:
            console.print(Panel(
                "[yellow]No pending tasks. Press [t] to add a new task![/]",
                border_style="yellow"
            ))

        console.print()

        # Recent profiles
        if recent_profiles:
            profiles_table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            profiles_table.add_column("Name", style="cyan", width=20)
            profiles_table.add_column("Email", style="blue", width=25)
            profiles_table.add_column("Phone", style="green", width=15)
            profiles_table.add_column("Seniority", style="yellow", width=12)
            profiles_table.add_column("Generation", style="magenta", width=10)
            profiles_table.add_column("Company", style="green", width=20)
            profiles_table.add_column("Skills", style="dim", no_wrap=False, width=20)
            profiles_table.add_column("Tags", style="yellow", no_wrap=False)

            for p in recent_profiles:
                # Email (truncated if too long)
                email_display = p.email[:23] + "..." if p.email and len(p.email) > 23 else (p.email or "-")

                # Phone
                phone_display = p.phone or "-"

                # Generation
                generation_display = p.generation.title() if p.generation else "-"

                # Company
                company_display = p.company.name[:18] + "..." if p.company and len(p.company.name) > 18 else (p.company.name if p.company else "-")

                # Skills (Good at - truncated)
                skills_display = p.good_at[:18] + "..." if p.good_at and len(p.good_at) > 18 else (p.good_at or "-")

                # Tags (show first 2)
                if p.tags:
                    tag_names = [t.name for t in p.tags[:2]]
                    if len(p.tags) > 2:
                        tag_names.append(f"+{len(p.tags)-2}")
                    tags_display = ", ".join(tag_names)
                else:
                    tags_display = "-"

                profiles_table.add_row(
                    p.name,
                    email_display,
                    phone_display,
                    p.seniority.title(),
                    generation_display,
                    company_display,
                    skills_display,
                    tags_display
                )

            console.print(Panel(profiles_table, title="[bold cyan]Recent Profiles[/]", border_style="cyan"))
        else:
            console.print(Panel(
                "[yellow]No profiles yet. Press [2] to add your first contact![/]",
                border_style="yellow"
            ))

        console.print()

        # Get action - single key press
        console.print("[dim]Press a key (t/c/e/d/v/r for tasks, 1-9 for navigation, Enter to continue):[/]")
        action = get_single_key()

        # Handle Enter key (returns '\r' or '\n')
        if action in ['\r', '\n', '']:
            session.close()
            return None

        # Check if user wants to navigate to another menu (numbers 1-9 or q)
        # Map numbers to view names
        nav_map = {
            '1': 'Dashboard',
            '2': 'Profiles',
            '3': 'Companies',
            '4': 'Network & Relationships',
            '5': 'Search',
            '6': 'Tags',
            '7': 'Workshop',
            '8': 'Export',
            '9': 'Import',
            'q': 'Exit',
            'Q': 'Exit'
        }

        if action in nav_map:
            session.close()
            return nav_map[action]
        elif action.lower() == 't':
            add_task_interactive()
        elif action.lower() == 'c':
            if upcoming_tasks:
                console.print("[cyan]Enter task number to complete (or press Enter to cancel):[/]")
                task_num = questionary.text(
                    "",
                    style=custom_style
                ).ask()
                if task_num:
                    try:
                        idx = int(task_num) - 1
                        if 0 <= idx < len(upcoming_tasks):
                            complete_task_interactive(upcoming_tasks[idx].id)
                    except ValueError:
                        pass
        elif action.lower() == 'e':
            if upcoming_tasks:
                console.print("[cyan]Enter task number to edit (or press Enter to cancel):[/]")
                task_num = questionary.text(
                    "",
                    style=custom_style
                ).ask()
                if task_num:
                    try:
                        idx = int(task_num) - 1
                        if 0 <= idx < len(upcoming_tasks):
                            edit_task_interactive(upcoming_tasks[idx].id)
                    except ValueError:
                        pass
        elif action.lower() == 'd':
            if upcoming_tasks:
                console.print("[cyan]Enter task number to delete (or press Enter to cancel):[/]")
                task_num = questionary.text(
                    "",
                    style=custom_style
                ).ask()
                if task_num:
                    try:
                        idx = int(task_num) - 1
                        if 0 <= idx < len(upcoming_tasks):
                            delete_task_interactive(upcoming_tasks[idx].id)
                    except ValueError:
                        pass
        elif action.lower() == 'v':
            tasks_menu()
        elif action.lower() == 'r':
            continue

    session.close()


def profiles_menu():
    """Show profiles list with action shortcuts in top bar"""
    session = get_session()

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Profiles"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[a] Add", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[d] Delete", style="red")
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
            # Display profiles list with all information
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=3)
            table.add_column("Name", style="cyan", no_wrap=False, width=15)
            table.add_column("Seniority", style="blue", width=10)
            table.add_column("Email", style="dim", no_wrap=False, width=20)
            table.add_column("Phone", style="dim", width=13)
            table.add_column("Company", style="green", no_wrap=False, width=15)
            table.add_column("Gen", style="magenta", width=8)
            table.add_column("M", style="cyan", width=3)  # Married
            table.add_column("C", style="cyan", width=3)  # Children
            table.add_column("Skills", style="yellow", no_wrap=False, width=20)
            table.add_column("Tags", style="yellow", no_wrap=False, width=15)
            table.add_column("Notes", style="dim", no_wrap=False, width=20)

            for idx, p in enumerate(profiles, 1):
                company = p.company.name if p.company else "-"

                # Tags (truncate if too long)
                tags = ", ".join([t.name for t in p.tags[:2]]) if p.tags else "-"
                if len(p.tags) > 2:
                    tags += f" +{len(p.tags)-2}"

                # Email (truncate if too long)
                email = p.email if p.email else "-"
                if email != "-" and len(email) > 20:
                    email = email[:17] + "..."

                # Phone
                phone = p.phone if p.phone else "-"

                # Generation
                generation = p.generation if p.generation else "-"

                # Married and Children status
                married = "✓" if p.married else "-"
                children = "✓" if p.has_children else "-"

                # Skills (from good_at field, truncate if too long)
                skills = p.good_at if p.good_at else "-"
                if skills != "-" and len(skills) > 20:
                    skills = skills[:17] + "..."

                # Notes (truncate if too long)
                notes = p.notes if p.notes else "-"
                if notes != "-" and len(notes) > 20:
                    notes = notes[:17] + "..."

                table.add_row(
                    str(idx),
                    p.name,
                    p.seniority.title(),
                    email,
                    phone,
                    company,
                    generation,
                    married,
                    children,
                    skills,
                    tags,
                    notes
                )

            console.print(table)
            console.print(f"\n[dim]{len(profiles)} profile(s) total[/]")
        else:
            console.print(Panel(
                "[yellow]No profiles yet. Press 'a' to add your first contact![/]",
                border_style="yellow"
            ))

        console.print()

        # Action prompt with single-key input
        action = get_single_key()

        # Navigation map for quick access
        nav_map = {
            '1': 'Dashboard',
            '2': 'Profiles',
            '3': 'Companies',
            '4': 'Network & Relationships',
            '5': 'Search',
            '6': 'Tags',
            '7': 'Workshop',
            'q': 'Exit',
            'Q': 'Exit'
        }

        # Check for navigation keys first
        if action in nav_map:
            session.close()
            return nav_map[action]

        # Empty input (Enter) = back to dashboard
        if action == '\r' or action == '\n':
            break

        if action.lower() == 'a':
            add_profile_interactive()
        elif action.lower() == 'e':
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
        elif action.lower() == 'd':
            # Delete a profile - show selection menu
            if not profiles:
                console.print("[yellow]No profiles to delete[/]")
                import time
                time.sleep(1)
                continue

            # Quick selection for delete
            profile_choices = [{'name': f"{idx+1}. {p.name}", 'value': p.id} for idx, p in enumerate(profiles)]
            profile_choices.append({'name': '← Cancel', 'value': None})

            profile_id = questionary.select(
                "Select profile to delete:",
                choices=profile_choices,
                style=custom_style
            ).ask()

            if profile_id:
                profile = session.query(Profile).filter(Profile.id == profile_id).first()
                if profile:
                    if questionary.confirm(f"Are you sure you want to delete {profile.name}?", style=custom_style, default=False).ask():
                        session.delete(profile)
                        session.commit()
                        console.print(f"\n[green]✓ Deleted {profile.name}[/]\n")
                        questionary.press_any_key_to_continue().ask()
        elif action.lower() == 's':
            search_interactive()
        elif action.lower() == 'r':
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

        # Show top navigation bar
        console.print(render_top_bar("Companies"))
        console.print()

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
            title="[bold cyan]🏢 Companies[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Get companies
        companies = session.query(Company).order_by(Company.name).all()

        if companies:
            # Display companies list with all information
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=3)
            table.add_column("Name", style="cyan", no_wrap=False, width=20)
            table.add_column("Industry", style="blue", no_wrap=False, width=15)
            table.add_column("Size", style="magenta", width=12)
            table.add_column("Location", style="yellow", no_wrap=False, width=18)
            table.add_column("Website", style="dim", no_wrap=False, width=25)
            table.add_column("Profiles", justify="right", style="green", width=8)
            table.add_column("Notes", style="dim", no_wrap=False, width=25)

            for idx, c in enumerate(companies, 1):
                # Industry
                industry = c.industry if c.industry else "-"

                # Size
                size = c.size if c.size else "-"

                # Location
                location = c.location if c.location else "-"

                # Website (truncate if too long)
                website = c.website if c.website else "-"
                if website != "-" and len(website) > 25:
                    website = website[:22] + "..."

                # Profiles count
                profiles_count = str(len(c.profiles))

                # Notes (truncate if too long)
                notes = c.notes if c.notes else "-"
                if notes != "-" and len(notes) > 25:
                    notes = notes[:22] + "..."

                table.add_row(
                    str(idx),
                    c.name,
                    industry,
                    size,
                    location,
                    website,
                    profiles_count,
                    notes
                )

            console.print(table)
            console.print(f"\n[dim]{len(companies)} company(ies) total[/]")
        else:
            console.print(Panel(
                "[yellow]No companies yet. Press 'a' to add one![/]",
                border_style="yellow"
            ))

        console.print()

        # Action prompt with single-key input
        action = get_single_key()

        # Navigation map for quick access
        nav_map = {
            '1': 'Dashboard',
            '2': 'Profiles',
            '3': 'Companies',
            '4': 'Network & Relationships',
            '5': 'Search',
            '6': 'Tags',
            '7': 'Workshop',
            'q': 'Exit',
            'Q': 'Exit'
        }

        # Check for navigation keys first
        if action in nav_map:
            session.close()
            return nav_map[action]

        # Empty input (Enter) = back to dashboard
        if action == '\r' or action == '\n':
            break

        if action.lower() == 'a':
            add_company_interactive()
        elif action.lower() == 'e':
            edit_company_menu()
        elif action.lower() == 'd':
            # Delete a company - show selection menu
            if not companies:
                console.print("[yellow]No companies to delete[/]")
                import time
                time.sleep(1)
                continue

            # Quick selection for delete
            company_choices = [{'name': f"{idx+1}. {c.name} ({len(c.profiles)} profiles)", 'value': c.id} for idx, c in enumerate(companies)]
            company_choices.append({'name': '← Cancel', 'value': None})

            company_id = questionary.select(
                "Select company to delete:",
                choices=company_choices,
                style=custom_style
            ).ask()

            if company_id:
                company = session.query(Company).filter(Company.id == company_id).first()
                if company:
                    profile_count = len(company.profiles)
                    if questionary.confirm(f"Are you sure you want to delete {company.name}? (Has {profile_count} profile(s))", style=custom_style, default=False).ask():
                        session.delete(company)
                        session.commit()
                        console.print(f"\n[green]✓ Deleted {company.name}[/]\n")
                        questionary.press_any_key_to_continue().ask()
        elif action.lower() == 'r':
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

        # Show top navigation bar
        console.print(render_top_bar("Tags"))
        console.print()

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

        # Action prompt with single-key input
        action = get_single_key()

        # Navigation map for quick access
        nav_map = {
            '1': 'Dashboard',
            '2': 'Profiles',
            '3': 'Companies',
            '4': 'Network & Relationships',
            '5': 'Search',
            '6': 'Tags',
            '7': 'Workshop',
            'q': 'Exit',
            'Q': 'Exit'
        }

        # Check for navigation keys first
        if action in nav_map:
            session.close()
            return nav_map[action]

        # Empty input (Enter) = back to dashboard
        if action == '\r' or action == '\n':
            break

        if action.lower() == 'a':
            add_tag_interactive()
        elif action.lower() == 'e':
            edit_tag_interactive()
        elif action.lower() == 'd':
            delete_tag_interactive()
        elif action.lower() == 'r':
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


def network_and_relationships_menu():
    """Combined view showing network map on top and relationships list below"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship
    import math

    session = get_session()
    view_filter = 'all'  # 'all', 'profile', 'company'
    show_map = True  # Toggle to show/hide map

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Network & Relationships"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[m] Map: ", style="cyan")
        actions_text.append("ON" if show_map else "OFF", style="bold green" if show_map else "bold dim")
        actions_text.append(" • ", style="dim")
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

        filter_label = ""
        if view_filter == 'profile':
            filter_label = " (Profile Only)"
        elif view_filter == 'company':
            filter_label = " (Company Only)"

        console.print(Panel(
            actions_text,
            title=f"[bold cyan]🗺️  Network & Relationships{filter_label}[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Show network map if enabled
        if show_map:
            profiles = session.query(Profile).all()
            companies = session.query(Company).all()
            profile_relationships = session.query(ProfileRelationship).all()
            company_relationships = session.query(CompanyRelationship).all()

            if profiles or companies:
                # Build network structure
                nodes = []
                node_map = {}
                edges = []

                # Add profile nodes
                for profile in profiles:
                    node_id = f"p_{profile.id}"
                    node_idx = len(nodes)
                    node_map[node_id] = node_idx
                    nodes.append({
                        'id': node_id,
                        'name': profile.name[:10],  # Shorter for compact view
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
                        'name': company.name[:10],
                        'type': 'company',
                        'entity': company
                    })

                # Add edges
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

                # Add profile-company edges
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

                # Compact circular layout
                width = 80
                height = 20
                center_x = width // 2
                center_y = height // 2
                radius = min(width // 2 - 12, height // 2 - 2)

                # Position nodes
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

                # Draw edges
                for edge in edges:
                    from_pos = positions[edge['from']]
                    to_pos = positions[edge['to']]

                    x0, y0 = from_pos
                    x1, y1 = to_pos

                    dx = abs(x1 - x0)
                    dy = abs(y1 - y0)
                    sx = 1 if x0 < x1 else -1
                    sy = 1 if y0 < y1 else -1
                    err = dx - dy

                    x, y = x0, y0
                    steps = 0
                    max_steps = width + height

                    while steps < max_steps:
                        if 0 <= y < height and 0 <= x < width:
                            if edge['type'] == 'works_at':
                                char = '·'
                            elif edge['bidirectional']:
                                char = '═'
                            else:
                                char = '─'

                            if canvas[y][x] == ' ' or canvas[y][x] in ['·', '─']:
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

                # Draw nodes
                for i, (pos, node) in enumerate(zip(positions, nodes)):
                    x, y = pos
                    if 0 <= y < height and 0 <= x < width:
                        icon = '👥' if node['type'] == 'profile' else '🏢'
                        # For emoji, just place the icon (it takes 2 char width)
                        if x < width:
                            canvas[y][x] = icon

                # Render canvas
                map_lines = []
                for row in canvas:
                    map_lines.append(''.join(row))

                map_text = '\n'.join(map_lines)

                # Add legend
                legend = Text()
                legend.append("👥 Profile", style="cyan")
                legend.append("  ", style="dim")
                legend.append("🏢 Company", style="green")
                legend.append("  ", style="dim")
                legend.append("─ Connection", style="dim")
                legend.append("  ", style="dim")
                legend.append("═ Bidirectional", style="dim")
                legend.append("  ", style="dim")
                legend.append("· Works at", style="dim")

                console.print(Panel(
                    map_text,
                    title="[bold cyan]Network Map[/]",
                    subtitle=legend,
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
            table.add_column("From", style="cyan", no_wrap=False)
            table.add_column("→", style="yellow", width=3)
            table.add_column("Relationship", style="yellow")
            table.add_column("To", style="cyan", no_wrap=False)
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

            console.print(Panel(
                table,
                title="[bold cyan]Relationships[/]",
                border_style="cyan",
                box=box.SIMPLE
            ))

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

        # Action prompt with single-key input
        action = get_single_key()

        # Navigation map for quick access
        nav_map = {
            '1': 'Dashboard',
            '2': 'Profiles',
            '3': 'Companies',
            '4': 'Network & Relationships',
            '5': 'Search',
            '6': 'Tags',
            '7': 'Workshop',
            'q': 'Exit',
            'Q': 'Exit'
        }

        # Check for navigation keys first
        if action in nav_map:
            session.close()
            return nav_map[action]

        # Empty input (Enter) = back to dashboard
        if action == '\r' or action == '\n':
            break
        elif action.lower() == 'm':
            show_map = not show_map
        elif action.lower() == 'a':
            create_relationship_interactive()
        elif action.lower() == 'e':
            # Combined list for editing
            all_rels = []
            if display_profile:
                all_rels.extend([('profile', rel) for rel in profile_rels])
            if display_company:
                all_rels.extend([('company', rel) for rel in company_rels])

            if all_rels:
                rel_num = questionary.text(
                    "Enter relationship number to edit:",
                    style=custom_style
                ).ask()
                try:
                    idx_val = int(rel_num) - 1
                    if 0 <= idx_val < len(all_rels):
                        rel_type, rel = all_rels[idx_val]
                        if rel_type == 'profile':
                            edit_profile_relationship_interactive(rel.id)
                        else:
                            edit_company_relationship_interactive(rel.id)
                except ValueError:
                    pass
        elif action.lower() == 'd':
            # Combined list for deleting
            all_rels = []
            if display_profile:
                all_rels.extend([('profile', rel) for rel in profile_rels])
            if display_company:
                all_rels.extend([('company', rel) for rel in company_rels])

            if all_rels:
                rel_num = questionary.text(
                    "Enter relationship number to delete:",
                    style=custom_style
                ).ask()
                try:
                    idx_val = int(rel_num) - 1
                    if 0 <= idx_val < len(all_rels):
                        rel_type, rel = all_rels[idx_val]
                        if rel_type == 'profile':
                            delete_profile_relationship(rel.id)
                        else:
                            delete_company_relationship(rel.id)
                except ValueError:
                    pass
        elif action.lower() == 'p':
            view_filter = 'profile' if view_filter != 'profile' else 'all'
        elif action.lower() == 'c':
            view_filter = 'company' if view_filter != 'company' else 'all'
        elif action.lower() == 'r':
            continue

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
    while True:
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

        # Action menu
        actions = [
            "📝 Edit Company",
            "🗑️  Delete Company",
            "← Back to List"
        ]

        action = questionary.select(
            "What would you like to do?",
            choices=actions,
            style=custom_style
        ).ask()

        if not action or action == "← Back to List":
            break

        elif action == "📝 Edit Company":
            edit_company_interactive(company, session)
            # Refresh company data after edit
            session.refresh(company)

        elif action == "🗑️  Delete Company":
            if questionary.confirm(f"Are you sure you want to delete {company.name}?", style=custom_style, default=False).ask():
                session.delete(company)
                session.commit()
                console.print(f"\n[green]✓ Deleted {company.name}[/]\n")
                questionary.press_any_key_to_continue().ask()
                break


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
    notes = questionary.text("Notes (optional):", style=custom_style).ask()

    session = get_session()
    try:
        new_company = Company(
            name=name,
            industry=industry or None,
            size=size or None,
            location=location or None,
            website=website or None,
            notes=notes or None
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

    # Show top navigation bar
    console.print(render_top_bar("Search"))
    console.print()

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


def workshop_menu():
    """Workshop - Analysis and problem-solving tools"""
    session = get_session()

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Workshop"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[1] Network Health", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[2] Key Connectors", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[3] Isolated Nodes", style="red")
        actions_text.append(" • ", style="dim")
        actions_text.append("[4] Relationship Health", style="magenta")
        actions_text.append(" • ", style="dim")
        actions_text.append("[5] Gap Analysis", style="cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[6] Recommendations", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[Enter] Back", style="dim white")

        console.print(Panel(
            actions_text,
            title="[bold cyan]🔧 Workshop - Analysis Tools[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()
        
        console.print(Panel(
            "[bold yellow]Problem-Solving Toolkit[/]\n"
            "[dim]Analyze your network, identify issues, and get actionable recommendations[/]",
            border_style="yellow",
            box=box.SIMPLE
        ))
        console.print()

        console.print()

        # Action prompt with single-key input
        action = get_single_key()

        # Navigation map for quick access
        nav_map = {
            '1': 'Dashboard',
            '2': 'Profiles',
            '3': 'Companies',
            '4': 'Network & Relationships',
            '5': 'Search',
            '6': 'Tags',
            '7': 'Workshop',
            'q': 'Exit',
            'Q': 'Exit'
        }

        # Check for navigation keys first - but workshop uses 1-6 for tools, so only check for 7 and q
        if action == '7' or action.lower() == 'q':
            session.close()
            return nav_map.get(action.lower(), nav_map.get(action))

        # Empty input (Enter) = back to dashboard
        if action == '\r' or action == '\n':
            break

        if action == '1':
            analyze_network_health(session)
        elif action == '2':
            find_key_connectors(session)
        elif action == '3':
            find_isolated_nodes(session)
        elif action == '4':
            relationship_health_check(session)
        elif action == '5':
            gap_analysis(session)
        elif action == '6':
            get_recommendations(session)
        else:
            console.print("[yellow]Invalid option. Try again.[/]")
            time.sleep(1)

    session.close()


def analyze_network_health(session):
    """Analyze overall network health and provide metrics"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship

    console.clear()
    console.print(Panel(
        "[bold green]🏥 Network Health Analysis[/]\n"
        "[dim]Overall state of your professional network[/]",
        border_style="green"
    ))
    console.print()

    # Gather data
    profiles = session.query(Profile).all()
    companies = session.query(Company).all()
    profile_rels = session.query(ProfileRelationship).all()
    company_rels = session.query(CompanyRelationship).all()

    if not profiles:
        console.print("[yellow]No data to analyze. Add some profiles first![/]")
        questionary.press_any_key_to_continue().ask()
        return

    # Calculate metrics
    total_nodes = len(profiles) + len(companies)
    total_relationships = len(profile_rels) + len(company_rels)

    # Connection density
    max_possible_profile_connections = len(profiles) * (len(profiles) - 1) / 2 if len(profiles) > 1 else 1
    profile_density = (len(profile_rels) / max_possible_profile_connections * 100) if max_possible_profile_connections > 0 else 0

    # Relationship status distribution
    good_rels = len([r for r in profile_rels + company_rels if r.status == "Good"])
    bad_rels = len([r for r in profile_rels + company_rels if r.status == "Bad"])
    neutral_rels = len([r for r in profile_rels + company_rels if r.status == "No Interest"])

    # Profile completeness
    complete_profiles = len([p for p in profiles if p.email and p.company_id and p.tags])
    completeness_rate = (complete_profiles / len(profiles) * 100) if profiles else 0

    # Connected vs isolated
    connected_profiles = set()
    for rel in profile_rels:
        connected_profiles.add(rel.from_profile_id)
        connected_profiles.add(rel.to_profile_id)
    for p in profiles:
        if p.company_id:
            connected_profiles.add(p.id)
    
    isolated_profiles = len(profiles) - len(connected_profiles)
    connectivity_rate = (len(connected_profiles) / len(profiles) * 100) if profiles else 0

    # Display health metrics
    console.print("[bold cyan]Network Size:[/]")
    table = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
    table.add_column(style="cyan", width=30)
    table.add_column(style="white")
    
    table.add_row("Total Nodes:", f"{total_nodes} ({len(profiles)} profiles, {len(companies)} companies)")
    table.add_row("Total Relationships:", str(total_relationships))
    table.add_row("Average Connections:", f"{total_relationships / len(profiles):.1f} per profile" if profiles else "0")
    
    console.print(table)
    console.print()

    # Health scores with color coding
    console.print("[bold cyan]Health Scores:[/]")
    health_table = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
    health_table.add_column(style="cyan", width=30)
    health_table.add_column(style="white", width=50)

    # Connectivity score
    if connectivity_rate >= 75:
        conn_color = "green"
        conn_status = "Excellent ✓"
    elif connectivity_rate >= 50:
        conn_color = "yellow"
        conn_status = "Good"
    else:
        conn_color = "red"
        conn_status = "Needs Improvement"
    
    health_table.add_row("Connectivity:", f"[{conn_color}]{connectivity_rate:.0f}% {conn_status}[/]")

    # Density score
    if profile_density >= 20:
        dens_color = "green"
        dens_status = "Well Connected ✓"
    elif profile_density >= 10:
        dens_color = "yellow"
        dens_status = "Moderate"
    else:
        dens_color = "red"
        dens_status = "Sparse"
    
    health_table.add_row("Network Density:", f"[{dens_color}]{profile_density:.1f}% {dens_status}[/]")

    # Completeness score
    if completeness_rate >= 75:
        comp_color = "green"
        comp_status = "Excellent ✓"
    elif completeness_rate >= 50:
        comp_color = "yellow"
        comp_status = "Good"
    else:
        comp_color = "red"
        comp_status = "Needs Work"
    
    health_table.add_row("Data Completeness:", f"[{comp_color}]{completeness_rate:.0f}% {comp_status}[/]")

    # Relationship health
    if total_relationships > 0:
        good_percentage = (good_rels / total_relationships * 100)
        if good_percentage >= 75:
            rel_color = "green"
            rel_status = "Healthy ✓"
        elif good_percentage >= 50:
            rel_color = "yellow"
            rel_status = "Fair"
        else:
            rel_color = "red"
            rel_status = "Attention Needed"
        
        health_table.add_row("Relationship Health:", f"[{rel_color}]{good_percentage:.0f}% positive {rel_status}[/]")

    console.print(health_table)
    console.print()

    # Issues and alerts
    issues = []
    if isolated_profiles > 0:
        issues.append(f"[red]• {isolated_profiles} isolated profile(s) with no connections[/]")
    if bad_rels > 0:
        issues.append(f"[red]• {bad_rels} relationship(s) marked as 'Bad'[/]")
    if completeness_rate < 50:
        issues.append(f"[yellow]• Only {complete_profiles}/{len(profiles)} profiles have complete information[/]")
    if profile_density < 5:
        issues.append(f"[yellow]• Low network density - consider adding more connections[/]")

    if issues:
        console.print("[bold red]⚠ Issues Detected:[/]")
        for issue in issues:
            console.print(issue)
        console.print()

    # Overall health score
    overall_score = (connectivity_rate + completeness_rate + (good_rels / total_relationships * 100 if total_relationships > 0 else 0)) / 3
    
    if overall_score >= 75:
        overall_color = "green"
        overall_status = "EXCELLENT"
    elif overall_score >= 50:
        overall_color = "yellow"
        overall_status = "GOOD"
    else:
        overall_color = "red"
        overall_status = "NEEDS IMPROVEMENT"

    console.print(Panel(
        f"[bold {overall_color}]Overall Health Score: {overall_score:.0f}%[/]\n"
        f"[{overall_color}]Status: {overall_status}[/]",
        border_style=overall_color,
        title="[bold]Network Health Summary[/]"
    ))

    console.print()
    questionary.press_any_key_to_continue().ask()


def find_key_connectors(session):
    """Identify the most connected and influential people in the network"""
    from leadsauce.models.relationship import ProfileRelationship

    console.clear()
    console.print(Panel(
        "[bold yellow]⭐ Key Connectors Analysis[/]\n"
        "[dim]Identify your most connected and influential contacts[/]",
        border_style="yellow"
    ))
    console.print()

    profiles = session.query(Profile).all()
    profile_rels = session.query(ProfileRelationship).all()

    if not profiles:
        console.print("[yellow]No profiles to analyze.[/]")
        questionary.press_any_key_to_continue().ask()
        return

    # Calculate connection counts for each profile
    connection_counts = {}
    for profile in profiles:
        count = 0
        # Count outgoing relationships
        count += len([r for r in profile_rels if r.from_profile_id == profile.id])
        # Count incoming relationships
        count += len([r for r in profile_rels if r.to_profile_id == profile.id])
        # Count company connection
        if profile.company_id:
            count += 1
        
        connection_counts[profile.id] = count

    # Sort by connection count
    sorted_profiles = sorted(profiles, key=lambda p: connection_counts[p.id], reverse=True)

    # Display top connectors
    if sorted_profiles:
        console.print("[bold cyan]🌟 Top Connectors:[/]\n")
        
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("Name", style="cyan")
        table.add_column("Connections", style="yellow", justify="right")
        table.add_column("Company", style="green")
        table.add_column("Seniority", style="blue")

        for i, profile in enumerate(sorted_profiles[:10], 1):
            company = profile.company.name if profile.company else "-"
            connections = connection_counts[profile.id]
            
            # Add medal emojis for top 3
            if i == 1:
                rank = "🥇 1"
            elif i == 2:
                rank = "🥈 2"
            elif i == 3:
                rank = "🥉 3"
            else:
                rank = f"   {i}"
            
            table.add_row(rank, profile.name, str(connections), company, profile.seniority.title())

        console.print(table)
        console.print()

        # Provide insights
        top_connector = sorted_profiles[0]
        top_count = connection_counts[top_connector.id]
        avg_connections = sum(connection_counts.values()) / len(profiles)

        console.print(Panel(
            f"[bold cyan]Insights:[/]\n"
            f"• Top connector: [yellow]{top_connector.name}[/] with {top_count} connections\n"
            f"• Average connections per profile: [yellow]{avg_connections:.1f}[/]\n"
            f"• These connectors are key influencers in your network",
            border_style="cyan",
            box=box.SIMPLE
        ))

    console.print()
    questionary.press_any_key_to_continue().ask()


def find_isolated_nodes(session):
    """Find profiles and companies with no connections"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship

    console.clear()
    console.print(Panel(
        "[bold red]🔴 Isolated Nodes Analysis[/]\n"
        "[dim]Find contacts and companies with no connections[/]",
        border_style="red"
    ))
    console.print()

    profiles = session.query(Profile).all()
    companies = session.query(Company).all()
    profile_rels = session.query(ProfileRelationship).all()
    company_rels = session.query(CompanyRelationship).all()

    # Find isolated profiles (no relationships and no company)
    connected_profile_ids = set()
    for rel in profile_rels:
        connected_profile_ids.add(rel.from_profile_id)
        connected_profile_ids.add(rel.to_profile_id)
    
    isolated_profiles = [p for p in profiles if p.id not in connected_profile_ids and not p.company_id]

    # Find isolated companies (no employees and no relationships)
    connected_company_ids = set()
    for rel in company_rels:
        connected_company_ids.add(rel.from_company_id)
        connected_company_ids.add(rel.to_company_id)
    for p in profiles:
        if p.company_id:
            connected_company_ids.add(p.company_id)
    
    isolated_companies = [c for c in companies if c.id not in connected_company_ids]

    # Display results
    if isolated_profiles:
        console.print(f"[bold red]👤 Isolated Profiles ({len(isolated_profiles)}):[/]\n")
        
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="red")
        table.add_column("Name", style="cyan")
        table.add_column("Seniority", style="yellow")
        table.add_column("Email", style="white")
        table.add_column("Tags", style="green")

        for profile in isolated_profiles[:20]:
            email = profile.email or "-"
            tags = ", ".join([t.name for t in profile.tags[:2]]) if profile.tags else "-"
            table.add_row(profile.name, profile.seniority.title(), email, tags)

        console.print(table)
        console.print()

        if len(isolated_profiles) > 20:
            console.print(f"[dim]... and {len(isolated_profiles) - 20} more[/]\n")

    if isolated_companies:
        console.print(f"[bold red]🏢 Isolated Companies ({len(isolated_companies)}):[/]\n")
        
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="red")
        table.add_column("Name", style="cyan")
        table.add_column("Industry", style="yellow")
        table.add_column("Location", style="white")

        for company in isolated_companies[:20]:
            industry = company.industry or "-"
            location = company.location or "-"
            table.add_row(company.name, industry, location)

        console.print(table)
        console.print()

    if not isolated_profiles and not isolated_companies:
        console.print(Panel(
            "[bold green]✓ No isolated nodes found![/]\n"
            "[dim]All profiles and companies have at least one connection.[/]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold yellow]Recommendations:[/]\n"
            f"• Add relationships for isolated profiles\n"
            f"• Assign companies to profiles without one\n"
            f"• Consider if these entries are still relevant",
            border_style="yellow",
            box=box.SIMPLE
        ))

    console.print()
    questionary.press_any_key_to_continue().ask()


def relationship_health_check(session):
    """Analyze relationship health and suggest improvements"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship

    console.clear()
    console.print(Panel(
        "[bold magenta]💔 Relationship Health Check[/]\n"
        "[dim]Analyze relationship quality and identify issues[/]",
        border_style="magenta"
    ))
    console.print()

    profile_rels = session.query(ProfileRelationship).all()
    company_rels = session.query(CompanyRelationship).all()

    if not profile_rels and not company_rels:
        console.print("[yellow]No relationships to analyze.[/]")
        questionary.press_any_key_to_continue().ask()
        return

    # Categorize relationships by status
    bad_profile_rels = [r for r in profile_rels if r.status == "Bad"]
    bad_company_rels = [r for r in company_rels if r.status == "Bad"]
    neutral_profile_rels = [r for r in profile_rels if r.status == "No Interest"]
    neutral_company_rels = [r for r in company_rels if r.status == "No Interest"]
    good_profile_rels = [r for r in profile_rels if r.status == "Good"]
    good_company_rels = [r for r in company_rels if r.status == "Good"]

    # Display status distribution
    console.print("[bold cyan]Relationship Status Distribution:[/]\n")
    
    status_table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
    status_table.add_column("Status", style="bold")
    status_table.add_column("Profile Relationships", justify="right")
    status_table.add_column("Company Relationships", justify="right")
    status_table.add_column("Total", justify="right", style="bold")

    status_table.add_row(
        "[green]Good[/]",
        str(len(good_profile_rels)),
        str(len(good_company_rels)),
        str(len(good_profile_rels) + len(good_company_rels))
    )
    status_table.add_row(
        "[red]Bad[/]",
        str(len(bad_profile_rels)),
        str(len(bad_company_rels)),
        str(len(bad_profile_rels) + len(bad_company_rels))
    )
    status_table.add_row(
        "[dim]No Interest[/]",
        str(len(neutral_profile_rels)),
        str(len(neutral_company_rels)),
        str(len(neutral_profile_rels) + len(neutral_company_rels))
    )

    console.print(status_table)
    console.print()

    # Show bad relationships that need attention
    if bad_profile_rels:
        console.print(f"[bold red]⚠ Bad Profile Relationships ({len(bad_profile_rels)}):[/]\n")
        
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="red")
        table.add_column("From", style="cyan")
        table.add_column("→", style="yellow", width=3)
        table.add_column("Type", style="yellow")
        table.add_column("To", style="cyan")
        table.add_column("Bidirectional", style="white")

        for rel in bad_profile_rels[:10]:
            arrow = "↔" if rel.bidirectional else "→"
            bidir = "Yes" if rel.bidirectional else "No"
            table.add_row(
                rel.from_profile.name,
                arrow,
                rel.relationship_type,
                rel.to_profile.name,
                bidir
            )

        console.print(table)
        console.print()

    if bad_company_rels:
        console.print(f"[bold red]⚠ Bad Company Relationships ({len(bad_company_rels)}):[/]\n")
        
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="red")
        table.add_column("From", style="cyan")
        table.add_column("→", style="yellow", width=3)
        table.add_column("Type", style="yellow")
        table.add_column("To", style="cyan")

        for rel in bad_company_rels[:10]:
            arrow = "↔" if rel.bidirectional else "→"
            table.add_row(
                rel.from_company.name,
                arrow,
                rel.relationship_type,
                rel.to_company.name
            )

        console.print(table)
        console.print()

    # Recommendations
    recommendations = []
    if len(bad_profile_rels) > 0:
        recommendations.append(f"• Review {len(bad_profile_rels)} bad profile relationship(s)")
    if len(bad_company_rels) > 0:
        recommendations.append(f"• Review {len(bad_company_rels)} bad company relationship(s)")
    if len(neutral_profile_rels) + len(neutral_company_rels) > len(profile_rels) + len(company_rels) * 0.3:
        recommendations.append(f"• High number of 'No Interest' relationships - consider cleanup")

    # One-way relationships that could be bidirectional
    oneway_profile_rels = [r for r in profile_rels if not r.bidirectional]
    if oneway_profile_rels:
        recommendations.append(f"• {len(oneway_profile_rels)} one-way relationships could potentially be bidirectional")

    if recommendations:
        console.print(Panel(
            "[bold yellow]Recommendations:[/]\n" + "\n".join(recommendations),
            border_style="yellow",
            box=box.SIMPLE
        ))
    else:
        console.print(Panel(
            "[bold green]✓ All relationships are in good standing![/]",
            border_style="green"
        ))

    console.print()
    questionary.press_any_key_to_continue().ask()


def gap_analysis(session):
    """Identify missing or incomplete data"""
    console.clear()
    console.print(Panel(
        "[bold cyan]📋 Gap Analysis[/]\n"
        "[dim]Find missing or incomplete information[/]",
        border_style="cyan"
    ))
    console.print()

    profiles = session.query(Profile).all()
    companies = session.query(Company).all()

    if not profiles and not companies:
        console.print("[yellow]No data to analyze.[/]")
        questionary.press_any_key_to_continue().ask()
        return

    # Analyze profiles
    profiles_no_email = [p for p in profiles if not p.email]
    profiles_no_company = [p for p in profiles if not p.company_id]
    profiles_no_tags = [p for p in profiles if not p.tags]
    profiles_no_phone = [p for p in profiles if not p.phone]
    profiles_incomplete = [p for p in profiles if not p.email or not p.company_id or not p.tags]

    # Analyze companies
    companies_no_industry = [c for c in companies if not c.industry]
    companies_no_location = [c for c in companies if not c.location]
    companies_no_employees = [c for c in companies if not any(p.company_id == c.id for p in profiles)]

    # Display gaps
    console.print("[bold yellow]📊 Data Completeness:[/]\n")

    gaps_table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
    gaps_table.add_column("Category", style="cyan", width=30)
    gaps_table.add_column("Count", style="yellow", justify="right")
    gaps_table.add_column("Percentage", style="white", justify="right")

    if profiles:
        gaps_table.add_row(
            "Profiles without email",
            str(len(profiles_no_email)),
            f"{len(profiles_no_email)/len(profiles)*100:.0f}%"
        )
        gaps_table.add_row(
            "Profiles without company",
            str(len(profiles_no_company)),
            f"{len(profiles_no_company)/len(profiles)*100:.0f}%"
        )
        gaps_table.add_row(
            "Profiles without tags",
            str(len(profiles_no_tags)),
            f"{len(profiles_no_tags)/len(profiles)*100:.0f}%"
        )
        gaps_table.add_row(
            "Profiles without phone",
            str(len(profiles_no_phone)),
            f"{len(profiles_no_phone)/len(profiles)*100:.0f}%"
        )
        gaps_table.add_row(
            "[bold]Incomplete profiles[/]",
            f"[bold]{len(profiles_incomplete)}[/]",
            f"[bold]{len(profiles_incomplete)/len(profiles)*100:.0f}%[/]"
        )

    if companies:
        gaps_table.add_row(
            "Companies without industry",
            str(len(companies_no_industry)),
            f"{len(companies_no_industry)/len(companies)*100:.0f}%"
        )
        gaps_table.add_row(
            "Companies without location",
            str(len(companies_no_location)),
            f"{len(companies_no_location)/len(companies)*100:.0f}%"
        )
        gaps_table.add_row(
            "Companies without employees",
            str(len(companies_no_employees)),
            f"{len(companies_no_employees)/len(companies)*100:.0f}%"
        )

    console.print(gaps_table)
    console.print()

    # Priority items to fix
    if profiles_incomplete:
        console.print(f"[bold red]🔴 High Priority ({len(profiles_incomplete)} profiles):[/]\n")
        
        table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="red")
        table.add_column("Name", style="cyan")
        table.add_column("Missing", style="yellow")

        for profile in profiles_incomplete[:10]:
            missing = []
            if not profile.email:
                missing.append("email")
            if not profile.company_id:
                missing.append("company")
            if not profile.tags:
                missing.append("tags")
            
            table.add_row(profile.name, ", ".join(missing))

        console.print(table)
        console.print()

    # Calculate completeness score
    if profiles:
        total_fields = len(profiles) * 3  # email, company, tags
        filled_fields = (len(profiles) - len(profiles_no_email) + 
                        len(profiles) - len(profiles_no_company) + 
                        len(profiles) - len(profiles_no_tags))
        completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0

        if completeness >= 75:
            color = "green"
            status = "Excellent ✓"
        elif completeness >= 50:
            color = "yellow"
            status = "Good"
        else:
            color = "red"
            status = "Needs Improvement"

        console.print(Panel(
            f"[bold {color}]Data Completeness Score: {completeness:.0f}%[/]\n"
            f"[{color}]Status: {status}[/]",
            border_style=color,
            title="[bold]Overall Score[/]"
        ))

    console.print()
    questionary.press_any_key_to_continue().ask()


def get_recommendations(session):
    """Get actionable recommendations based on network analysis"""
    from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship

    console.clear()
    console.print(Panel(
        "[bold blue]💡 Smart Recommendations[/]\n"
        "[dim]Actionable insights to improve your network[/]",
        border_style="blue"
    ))
    console.print()

    profiles = session.query(Profile).all()
    companies = session.query(Company).all()
    profile_rels = session.query(ProfileRelationship).all()
    company_rels = session.query(CompanyRelationship).all()

    if not profiles:
        console.print("[yellow]No data to analyze. Add some profiles first![/]")
        questionary.press_any_key_to_continue().ask()
        return

    recommendations = []

    # 1. Network expansion recommendations
    connected_profile_ids = set()
    for rel in profile_rels:
        connected_profile_ids.add(rel.from_profile_id)
        connected_profile_ids.add(rel.to_profile_id)
    
    isolated_count = len([p for p in profiles if p.id not in connected_profile_ids and not p.company_id])
    if isolated_count > 0:
        recommendations.append({
            'priority': 'HIGH',
            'category': '🔗 Network Expansion',
            'action': f'Connect {isolated_count} isolated profile(s)',
            'benefit': 'Increase network connectivity and discover new opportunities'
        })

    # 2. Relationship improvement
    bad_rels = [r for r in profile_rels + company_rels if r.status == "Bad"]
    if bad_rels:
        recommendations.append({
            'priority': 'HIGH',
            'category': '💔 Relationship Health',
            'action': f'Review and address {len(bad_rels)} bad relationship(s)',
            'benefit': 'Repair or remove damaged connections'
        })

    # 3. Data completeness
    incomplete_profiles = [p for p in profiles if not p.email or not p.company_id or not p.tags]
    if len(incomplete_profiles) > len(profiles) * 0.3:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': '📋 Data Quality',
            'action': f'Complete information for {len(incomplete_profiles)} profile(s)',
            'benefit': 'Better insights and more effective networking'
        })

    # 4. Key connector engagement
    connection_counts = {}
    for profile in profiles:
        count = len([r for r in profile_rels if r.from_profile_id == profile.id or r.to_profile_id == profile.id])
        if profile.company_id:
            count += 1
        connection_counts[profile.id] = count

    top_connectors = sorted(profiles, key=lambda p: connection_counts[p.id], reverse=True)[:3]
    if top_connectors and connection_counts[top_connectors[0].id] > 5:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': '⭐ Strategic Networking',
            'action': f'Leverage connections through {top_connectors[0].name}',
            'benefit': 'Access to broader network through key influencer'
        })

    # 5. Bidirectional opportunity
    oneway_rels = [r for r in profile_rels if not r.bidirectional and r.status == "Good"]
    if len(oneway_rels) > 3:
        recommendations.append({
            'priority': 'LOW',
            'category': '↔ Relationship Depth',
            'action': f'Convert {len(oneway_rels)} one-way to bidirectional relationships',
            'benefit': 'Strengthen existing connections'
        })

    # 6. Company clustering
    company_groups = defaultdict(list)
    for p in profiles:
        if p.company_id:
            company_groups[p.company_id].append(p)
    
    large_company_groups = [c for c, ps in company_groups.items() if len(ps) >= 3]
    if large_company_groups:
        recommendations.append({
            'priority': 'LOW',
            'category': '🏢 Internal Networks',
            'action': f'Create internal connections within {len(large_company_groups)} organization(s)',
            'benefit': 'Better understanding of organizational dynamics'
        })

    # Display recommendations
    if recommendations:
        # Group by priority
        high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
        medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
        low_priority = [r for r in recommendations if r['priority'] == 'LOW']

        if high_priority:
            console.print("[bold red]🔴 High Priority Actions:[/]\n")
            for rec in high_priority:
                console.print(Panel(
                    f"[bold yellow]{rec['category']}[/]\n"
                    f"[white]{rec['action']}[/]\n\n"
                    f"[dim]💡 Benefit: {rec['benefit']}[/]",
                    border_style="red",
                    box=box.SIMPLE
                ))
            console.print()

        if medium_priority:
            console.print("[bold yellow]🟡 Medium Priority Actions:[/]\n")
            for rec in medium_priority:
                console.print(Panel(
                    f"[bold yellow]{rec['category']}[/]\n"
                    f"[white]{rec['action']}[/]\n\n"
                    f"[dim]💡 Benefit: {rec['benefit']}[/]",
                    border_style="yellow",
                    box=box.SIMPLE
                ))
            console.print()

        if low_priority:
            console.print("[bold green]🟢 Low Priority Improvements:[/]\n")
            for rec in low_priority:
                console.print(Panel(
                    f"[bold cyan]{rec['category']}[/]\n"
                    f"[white]{rec['action']}[/]\n\n"
                    f"[dim]💡 Benefit: {rec['benefit']}[/]",
                    border_style="green",
                    box=box.SIMPLE
                ))
            console.print()

    else:
        console.print(Panel(
            "[bold green]🎉 Excellent![/]\n\n"
            "[white]Your network is in great shape. No immediate actions needed.[/]",
            border_style="green"
        ))
        console.print()

    console.print(Panel(
        "[dim]💡 Tip: Regularly check the Workshop for new insights as your network grows[/]",
        border_style="cyan",
        box=box.SIMPLE
    ))

    console.print()
    questionary.press_any_key_to_continue().ask()


# ============================================================================
# TASK MANAGEMENT
# ============================================================================

def detect_entities_in_text(text, session):
    """Detect mentions of profiles, companies, and tags in text"""
    if not text:
        return [], [], []

    text_lower = text.lower()

    # Detect profiles
    detected_profiles = []
    all_profiles = session.query(Profile).all()
    for profile in all_profiles:
        if profile.name.lower() in text_lower:
            detected_profiles.append(profile)

    # Detect companies
    detected_companies = []
    all_companies = session.query(Company).all()
    for company in all_companies:
        if company.name.lower() in text_lower:
            detected_companies.append(company)

    # Detect tags
    detected_tags = []
    all_tags = session.query(Tag).all()
    for tag in all_tags:
        if tag.name.lower() in text_lower:
            detected_tags.append(tag)

    return detected_profiles, detected_companies, detected_tags


def add_task_interactive():
    """Add a new task with smart entity detection"""
    session = get_session()

    try:
        console.clear()
        console.print(Panel(
            "[bold cyan]➕ Add New Task[/]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        console.print()

        # Get task title
        title = questionary.text(
            "Task title:",
            style=custom_style
        ).ask()

        if not title:
            console.print("[yellow]Task creation cancelled[/]")
            time.sleep(1)
            return

        # Get task description
        description = questionary.text(
            "Description (optional):",
            style=custom_style
        ).ask()

        # Combine title and description for entity detection
        full_text = f"{title} {description or ''}"

        # Smart entity detection
        detected_profiles, detected_companies, detected_tags = detect_entities_in_text(full_text, session)

        # Show detected entities
        if detected_profiles or detected_companies or detected_tags:
            console.print()
            console.print("[bold green]🔍 Detected entities:[/]")

            if detected_profiles:
                console.print(f"[cyan]Profiles:[/] {', '.join([p.name for p in detected_profiles])}")
            if detected_companies:
                console.print(f"[green]Companies:[/] {', '.join([c.name for c in detected_companies])}")
            if detected_tags:
                console.print(f"[yellow]Tags:[/] {', '.join([t.name for t in detected_tags])}")

            console.print()

        # Get priority
        priority = questionary.select(
            "Priority:",
            choices=["Low", "Medium", "High", "Urgent"],
            default="Medium",
            style=custom_style
        ).ask()

        # Get status
        status = questionary.select(
            "Status:",
            choices=["Pending", "In Progress", "Completed", "Cancelled"],
            default="Pending",
            style=custom_style
        ).ask()

        # Get due date
        due_date_option = questionary.select(
            "Due date:",
            choices=[
                "No due date",
                "Today",
                "Tomorrow",
                "In 3 days",
                "In 1 week",
                "In 1 month",
                "Custom"
            ],
            style=custom_style
        ).ask()

        due_date = None
        if due_date_option == "Today":
            due_date = datetime.now().replace(hour=23, minute=59, second=59)
        elif due_date_option == "Tomorrow":
            due_date = (datetime.now() + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif due_date_option == "In 3 days":
            due_date = (datetime.now() + timedelta(days=3)).replace(hour=23, minute=59, second=59)
        elif due_date_option == "In 1 week":
            due_date = (datetime.now() + timedelta(weeks=1)).replace(hour=23, minute=59, second=59)
        elif due_date_option == "In 1 month":
            due_date = (datetime.now() + timedelta(days=30)).replace(hour=23, minute=59, second=59)
        elif due_date_option == "Custom":
            date_str = questionary.text(
                "Enter date (YYYY-MM-DD):",
                style=custom_style
            ).ask()
            try:
                due_date = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            except:
                console.print("[yellow]Invalid date format, no due date set[/]")

        # Create task
        task = Task(
            title=title,
            description=description,
            priority=priority.lower(),
            status=status.lower().replace(" ", "_"),
            due_date=due_date
        )

        # Add detected entities
        task.profiles.extend(detected_profiles)
        task.companies.extend(detected_companies)
        task.tags.extend(detected_tags)

        # Ask if user wants to add more entities
        if questionary.confirm(
            "Add more profiles/companies/tags?",
            default=False,
            style=custom_style
        ).ask():

            # Add more profiles
            all_profiles = session.query(Profile).all()
            if all_profiles:
                profile_choices = [
                    {"name": f"{p.name} ({p.company.name if p.company else 'No company'})", "value": p.id}
                    for p in all_profiles if p not in detected_profiles
                ]

                if profile_choices:
                    console.print()
                    console.print("[bold cyan]📝 How to select profiles:[/]")
                    console.print("[dim]  • Use ↑↓ arrow keys to navigate[/]")
                    console.print("[dim]  • Press SPACE to select/deselect (● means selected)[/]")
                    console.print("[dim]  • Press ENTER when done (or press ENTER now to skip)[/]")
                    console.print()

                    selected_profile_ids = questionary.checkbox(
                        "Select profiles (SPACE=select, ENTER=done/skip):",
                        choices=profile_choices,
                        style=custom_style,
                        instruction="(↑↓ navigate, space to select, enter to finish or skip)"
                    ).ask()

                    if selected_profile_ids:
                        for pid in selected_profile_ids:
                            profile = session.query(Profile).get(pid)
                            if profile:
                                task.profiles.append(profile)

            # Add more companies
            all_companies = session.query(Company).all()
            if all_companies:
                company_choices = [
                    {"name": c.name, "value": c.id}
                    for c in all_companies if c not in detected_companies
                ]

                if company_choices:
                    console.print()
                    console.print("[bold cyan]📝 How to select companies:[/]")
                    console.print("[dim]  • Press SPACE to select/deselect (● means selected)[/]")
                    console.print("[dim]  • Press ENTER when done (or press ENTER now to skip)[/]")
                    console.print()

                    selected_company_ids = questionary.checkbox(
                        "Select companies (SPACE=select, ENTER=done/skip):",
                        choices=company_choices,
                        style=custom_style,
                        instruction="(↑↓ navigate, space to select, enter to finish or skip)"
                    ).ask()

                    if selected_company_ids:
                        for cid in selected_company_ids:
                            company = session.query(Company).get(cid)
                            if company:
                                task.companies.append(company)

            # Add more tags
            all_tags = session.query(Tag).all()
            if all_tags:
                tag_choices = [
                    {"name": t.name, "value": t.id}
                    for t in all_tags if t not in detected_tags
                ]

                if tag_choices:
                    console.print()
                    console.print("[bold cyan]📝 How to select tags:[/]")
                    console.print("[dim]  • Press SPACE to select/deselect (● means selected)[/]")
                    console.print("[dim]  • Press ENTER when done (or press ENTER now to skip)[/]")
                    console.print()

                    selected_tag_ids = questionary.checkbox(
                        "Select tags (SPACE=select, ENTER=done/skip):",
                        choices=tag_choices,
                        style=custom_style,
                        instruction="(↑↓ navigate, space to select, enter to finish or skip)"
                    ).ask()

                    if selected_tag_ids:
                        for tid in selected_tag_ids:
                            tag = session.query(Tag).get(tid)
                            if tag:
                                task.tags.append(tag)

        # Save task
        session.add(task)
        session.flush()  # Ensure relationships are persisted
        session.commit()

        # Refresh task to ensure all relationships are loaded
        session.refresh(task)

        console.print()
        console.print(Panel(
            f"[bold green]✓ Task '{task.title}' created successfully![/]",
            border_style="green"
        ))

        # Show summary
        console.print()
        console.print("[bold]Task Summary:[/]")
        console.print(f"[cyan]Title:[/] {task.title}")
        console.print(f"[cyan]Priority:[/] {task.priority.upper()}")
        console.print(f"[cyan]Status:[/] {task.status.replace('_', ' ').title()}")
        if task.due_date:
            console.print(f"[cyan]Due:[/] {task.due_date.strftime('%Y-%m-%d')}")
        if task.profiles:
            console.print(f"[cyan]Linked Profiles:[/] {', '.join([p.name for p in task.profiles])}")
        if task.companies:
            console.print(f"[cyan]Linked Companies:[/] {', '.join([c.name for c in task.companies])}")
        if task.tags:
            console.print(f"[cyan]Tags:[/] {', '.join([t.name for t in task.tags])}")

        console.print()
        time.sleep(2)

    except Exception as e:
        session.rollback()
        console.print(f"[red]Error creating task: {e}[/]")
        time.sleep(2)
    finally:
        session.close()


def tasks_menu():
    """Show tasks list with action shortcuts"""
    session = get_session()
    view_filter = 'all'  # 'all', 'pending', 'in_progress', 'completed', 'overdue'

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Dashboard"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[a] Add", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[e] Edit", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[c] Complete", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[d] Delete", style="red")
        actions_text.append(" • ", style="dim")
        actions_text.append("[f] Filter: ", style="cyan")
        actions_text.append(view_filter.replace('_', ' ').title(), style="bold cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[r] Refresh", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[Enter] Back", style="dim white")

        console.print(Panel(
            actions_text,
            title="[bold cyan]✅ Tasks[/]",
            border_style="cyan",
            box=box.SIMPLE
        ))
        console.print()

        # Get tasks based on filter
        from sqlalchemy.orm import joinedload
        query = session.query(Task).options(
            joinedload(Task.profiles),
            joinedload(Task.companies),
            joinedload(Task.tags)
        )

        if view_filter == 'pending':
            query = query.filter(Task.status == 'pending')
        elif view_filter == 'in_progress':
            query = query.filter(Task.status == 'in_progress')
        elif view_filter == 'completed':
            query = query.filter(Task.status == 'completed')
        elif view_filter == 'overdue':
            query = query.filter(
                Task.status.in_(['pending', 'in_progress']),
                Task.due_date < datetime.now()
            )

        tasks = query.order_by(Task.due_date.asc().nullsfirst(), Task.priority.desc()).all()

        if tasks:
            # Display tasks table
            table = Table(show_header=True, box=box.SIMPLE_HEAD, border_style="cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Title", style="cyan", no_wrap=False)
            table.add_column("Priority", width=8)
            table.add_column("Status", width=12)
            table.add_column("Due Date", width=12)
            table.add_column("Links", style="dim", width=10)

            for idx, task in enumerate(tasks, 1):
                # Priority color
                priority_color = {
                    'low': 'blue',
                    'medium': 'yellow',
                    'high': 'magenta',
                    'urgent': 'red bold'
                }.get(task.priority, 'white')

                # Status color
                status_color = {
                    'pending': 'yellow',
                    'in_progress': 'cyan',
                    'completed': 'green',
                    'cancelled': 'red'
                }.get(task.status, 'white')

                # Due date formatting
                due_display = ""
                if task.due_date:
                    due_str = task.due_date.strftime('%Y-%m-%d')
                    if task.is_overdue():
                        due_display = f"[red bold]{due_str} ⚠️[/]"
                    elif task.due_date.date() == datetime.now().date():
                        due_display = f"[yellow bold]{due_str}[/]"
                    else:
                        due_display = due_str
                else:
                    due_display = "-"

                # Links summary (show all: profiles, companies, and tags)
                link_parts = []
                if task.profiles:
                    link_parts.append(f"👥{len(task.profiles)}")
                if task.companies:
                    link_parts.append(f"🏢{len(task.companies)}")
                if task.tags:
                    link_parts.append(f"🏷️{len(task.tags)}")
                links_display = " ".join(link_parts) if link_parts else "-"

                table.add_row(
                    str(idx),
                    task.title[:50] + "..." if len(task.title) > 50 else task.title,
                    f"[{priority_color}]{task.priority.upper()}[/]",
                    f"[{status_color}]{task.status.replace('_', ' ').title()}[/]",
                    due_display,
                    links_display
                )

            console.print(table)
        else:
            console.print(Panel(
                f"[yellow]No {view_filter.replace('_', ' ')} tasks found[/]",
                border_style="yellow"
            ))

        console.print()

        # Get action
        action = questionary.text(
            "Action:",
            style=custom_style
        ).ask()

        if not action or action == "":
            break
        elif action.lower() == 'a':
            add_task_interactive()
        elif action.lower() == 'e':
            if tasks:
                task_num = questionary.text(
                    "Enter task number to edit:",
                    style=custom_style
                ).ask()
                try:
                    idx = int(task_num) - 1
                    if 0 <= idx < len(tasks):
                        edit_task_interactive(tasks[idx].id)
                except ValueError:
                    pass
        elif action.lower() == 'c':
            if tasks:
                task_num = questionary.text(
                    "Enter task number to complete:",
                    style=custom_style
                ).ask()
                try:
                    idx = int(task_num) - 1
                    if 0 <= idx < len(tasks):
                        complete_task_interactive(tasks[idx].id)
                except ValueError:
                    pass
        elif action.lower() == 'd':
            if tasks:
                task_num = questionary.text(
                    "Enter task number to delete:",
                    style=custom_style
                ).ask()
                try:
                    idx = int(task_num) - 1
                    if 0 <= idx < len(tasks):
                        delete_task_interactive(tasks[idx].id)
                except ValueError:
                    pass
        elif action.lower() == 'f':
            view_filter = questionary.select(
                "Filter tasks by:",
                choices=['all', 'pending', 'in_progress', 'completed', 'overdue'],
                style=custom_style
            ).ask()
        elif action.lower() == 'r':
            continue

    session.close()


def edit_task_interactive(task_id):
    """Edit an existing task"""
    session = get_session()

    try:
        task = session.query(Task).get(task_id)
        if not task:
            console.print("[red]Task not found[/]")
            time.sleep(1)
            return

        console.clear()
        console.print(Panel(
            f"[bold cyan]✏️ Edit Task: {task.title}[/]",
            border_style="cyan"
        ))
        console.print()

        # Edit title
        new_title = questionary.text(
            "Title:",
            default=task.title,
            style=custom_style
        ).ask()

        if new_title:
            task.title = new_title

        # Edit description
        new_description = questionary.text(
            "Description:",
            default=task.description or "",
            style=custom_style
        ).ask()

        task.description = new_description if new_description else None

        # Edit priority
        task.priority = questionary.select(
            "Priority:",
            choices=["low", "medium", "high", "urgent"],
            default=task.priority,
            style=custom_style
        ).ask()

        # Edit status
        task.status = questionary.select(
            "Status:",
            choices=["pending", "in_progress", "completed", "cancelled"],
            default=task.status,
            style=custom_style
        ).ask()

        # If status changed to completed, set completed_at
        if task.status == 'completed' and not task.completed_at:
            task.completed_at = datetime.now()

        # Edit linked entities
        edit_links = questionary.confirm(
            "Do you want to modify linked profiles/companies/tags?",
            default=False,
            style=custom_style
        ).ask()

        if edit_links:
            # Show current links
            console.print()
            console.print("[bold yellow]Current Links:[/]")
            if task.profiles:
                console.print(f"[cyan]Profiles:[/] {', '.join([p.name for p in task.profiles])}")
            else:
                console.print("[cyan]Profiles:[/] None")
            if task.companies:
                console.print(f"[green]Companies:[/] {', '.join([c.name for c in task.companies])}")
            else:
                console.print("[green]Companies:[/] None")
            if task.tags:
                console.print(f"[yellow]Tags:[/] {', '.join([t.name for t in task.tags])}")
            else:
                console.print("[yellow]Tags:[/] None")
            console.print()

            # Profiles
            all_profiles = session.query(Profile).all()
            if all_profiles:
                console.print()
                console.print("[bold cyan]📝 Select profiles:[/]")
                console.print("[dim]  • Current selections are pre-marked with ●[/]")
                console.print("[dim]  • Press SPACE to select/deselect[/]")
                console.print("[dim]  • Press ENTER when done[/]")
                console.print()

                current_profile_ids = [p.id for p in task.profiles]
                profile_choices = [
                    {"name": f"{p.name} ({p.company.name if p.company else 'No company'})",
                     "value": p.id,
                     "checked": p.id in current_profile_ids}
                    for p in all_profiles
                ]

                selected_profile_ids = questionary.checkbox(
                    "Select profiles (SPACE=select, ENTER=done):",
                    choices=profile_choices,
                    style=custom_style
                ).ask()

                # Update profiles
                task.profiles.clear()
                if selected_profile_ids:
                    for pid in selected_profile_ids:
                        profile = session.query(Profile).get(pid)
                        if profile:
                            task.profiles.append(profile)

            # Companies
            all_companies = session.query(Company).all()
            if all_companies:
                console.print()
                console.print("[bold cyan]📝 Select companies:[/]")
                console.print("[dim]  • Press SPACE to select/deselect[/]")
                console.print("[dim]  • Press ENTER when done[/]")
                console.print()

                current_company_ids = [c.id for c in task.companies]
                company_choices = [
                    {"name": c.name,
                     "value": c.id,
                     "checked": c.id in current_company_ids}
                    for c in all_companies
                ]

                selected_company_ids = questionary.checkbox(
                    "Select companies (SPACE=select, ENTER=done):",
                    choices=company_choices,
                    style=custom_style
                ).ask()

                # Update companies
                task.companies.clear()
                if selected_company_ids:
                    for cid in selected_company_ids:
                        company = session.query(Company).get(cid)
                        if company:
                            task.companies.append(company)

            # Tags
            all_tags = session.query(Tag).all()
            if all_tags:
                console.print()
                console.print("[bold cyan]📝 Select tags:[/]")
                console.print("[dim]  • Press SPACE to select/deselect[/]")
                console.print("[dim]  • Press ENTER when done[/]")
                console.print()

                current_tag_ids = [t.id for t in task.tags]
                tag_choices = [
                    {"name": t.name,
                     "value": t.id,
                     "checked": t.id in current_tag_ids}
                    for t in all_tags
                ]

                selected_tag_ids = questionary.checkbox(
                    "Select tags (SPACE=select, ENTER=done):",
                    choices=tag_choices,
                    style=custom_style
                ).ask()

                # Update tags
                task.tags.clear()
                if selected_tag_ids:
                    for tid in selected_tag_ids:
                        tag = session.query(Tag).get(tid)
                        if tag:
                            task.tags.append(tag)

        session.commit()

        console.print()
        console.print(Panel(
            "[bold green]✓ Task updated successfully![/]",
            border_style="green"
        ))
        time.sleep(1)

    except Exception as e:
        session.rollback()
        console.print(f"[red]Error updating task: {e}[/]")
        time.sleep(2)
    finally:
        session.close()


def complete_task_interactive(task_id):
    """Mark a task as completed"""
    session = get_session()

    try:
        task = session.query(Task).get(task_id)
        if not task:
            console.print("[red]Task not found[/]")
            time.sleep(1)
            return

        task.complete()
        session.commit()

        console.print()
        console.print(Panel(
            f"[bold green]✓ Task '{task.title}' marked as completed![/]",
            border_style="green"
        ))
        time.sleep(1)

    except Exception as e:
        session.rollback()
        console.print(f"[red]Error completing task: {e}[/]")
        time.sleep(2)
    finally:
        session.close()


def delete_task_interactive(task_id):
    """Delete a task"""
    session = get_session()

    try:
        task = session.query(Task).get(task_id)
        if not task:
            console.print("[red]Task not found[/]")
            time.sleep(1)
            return

        confirm = questionary.confirm(
            f"Are you sure you want to delete task '{task.title}'?",
            default=False,
            style=custom_style
        ).ask()

        if confirm:
            session.delete(task)
            session.commit()

            console.print()
            console.print(Panel(
                "[bold green]✓ Task deleted successfully![/]",
                border_style="green"
            ))
            time.sleep(1)

    except Exception as e:
        session.rollback()
        console.print(f"[red]Error deleting task: {e}[/]")
        time.sleep(2)
    finally:
        session.close()


def export_menu():
    """Export menu - Export data to CSV files"""
    from pathlib import Path
    from leadsauce.commands.export import (
        export_profiles, export_companies, export_tasks, export_interactions,
        export_profile_relationships, export_company_relationships, export_tags,
        export_reminders, export_teams, export_documents, export_activities,
        export_all_to_single_file
    )
    from leadsauce.utils.constants import APP_DIR

    session = get_session()

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Export"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[1] Export All Data", style="bold cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[2] Export Profiles", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[3] Export Companies", style="yellow")
        actions_text.append(" • ", style="dim")
        actions_text.append("[4] Export Tasks", style="magenta")
        actions_text.append(" • ", style="dim")
        actions_text.append("[5] Export Interactions", style="blue")
        actions_text.append(" • ", style="dim")
        actions_text.append("[6] More Options", style="white")
        console.print(Panel(actions_text, title="Export Options", border_style="cyan"))
        console.print()

        # Statistics
        try:
            profile_count = session.query(Profile).count()
            company_count = session.query(Company).count()
            task_count = session.query(Task).count()

            stats_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            stats_table.add_column("Entity Type", style="cyan", width=20)
            stats_table.add_column("Count", style="green", justify="right", width=10)

            stats_table.add_row("Profiles", str(profile_count))
            stats_table.add_row("Companies", str(company_count))
            stats_table.add_row("Tasks", str(task_count))

            console.print(stats_table)
            console.print()

            # Check if database is empty
            total_records = profile_count + company_count + task_count
            if total_records == 0:
                console.print(Panel(
                    "[yellow]⚠ Your database is empty![/]\n\n"
                    "Add some data first using the TUI or CLI:\n"
                    "  • Press [cyan]2[/cyan] for Profiles menu to add contacts\n"
                    "  • Press [cyan]3[/cyan] for Companies menu to add organizations\n"
                    "  • Or use CLI: [dim]leadsauce profile create --interactive[/dim]",
                    title="No Data to Export",
                    border_style="yellow"
                ))
                console.print()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load statistics: {e}[/]")
            console.print()

        # Handle keyboard shortcuts
        console.print("[dim]Press a number key or navigate with arrow keys[/]")
        console.print()

        # Create menu choices
        choices = [
            "📦 [1] Export All Data to CSV",
            "👥 [2] Export Profiles",
            "🏢 [3] Export Companies",
            "✅ [4] Export Tasks",
            "💬 [5] Export Interactions",
            "🔗 [6] Export Relationships",
            "🏷️  [7] Export Tags",
            "⏰ [8] Export Reminders",
            "📄 [9] Export Other Data",
            "🔙 Back to Dashboard"
        ]

        action = questionary.select(
            "Select export option:",
            choices=choices,
            style=custom_style
        ).ask()

        if not action:
            return None  # User cancelled (Ctrl+C)

        # Setup default output directory
        from pathlib import Path
        output_dir = Path.home() / 'Documents' / 'leadsauce' / 'exports' / datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if "Export All Data" in action:
                console.print()
                output_file = output_dir / 'leadsauce_export_all.csv'
                console.print(f"[cyan]Exporting all data to single file:[/]")
                console.print(f"[dim]{output_file}[/]")
                console.print()

                # Export to single CSV file
                total_exported = export_all_to_single_file(session, output_dir)

                if total_exported > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Export completed![/]\n\n"
                        f"Total records exported: {total_exported}\n"
                        f"File: {output_file.name}\n"
                        f"Location: {output_dir}",
                        border_style="green",
                        title="Export Complete"
                    ))
                else:
                    console.print()
                    console.print(Panel(
                        "[yellow]No data to export![/]\n\nAdd some profiles or companies first.",
                        border_style="yellow",
                        title="No Data"
                    ))

            elif "Export Profiles" in action:
                console.print()
                console.print(f"[cyan]Exporting profiles to: {output_dir}[/]")
                count = export_profiles(session, output_dir)
                if count > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Exported {count} profiles[/]\n\nLocation: {output_dir / 'profiles.csv'}",
                        border_style="green",
                        title="Export Complete"
                    ))
                else:
                    console.print()
                    console.print(Panel(
                        "[yellow]No profiles found in database.[/]\n\nAdd profiles first using the Profiles menu (press 2).",
                        border_style="yellow",
                        title="No Data"
                    ))

            elif "Export Companies" in action:
                console.print()
                console.print(f"[cyan]Exporting companies to: {output_dir}[/]")
                count = export_companies(session, output_dir)
                if count > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Exported {count} companies[/]\n\nLocation: {output_dir / 'companies.csv'}",
                        border_style="green",
                        title="Export Complete"
                    ))
                else:
                    console.print()
                    console.print(Panel(
                        "[yellow]No companies found in database.[/]\n\nAdd companies first using the Companies menu (press 3).",
                        border_style="yellow",
                        title="No Data"
                    ))

            elif "Export Tasks" in action:
                console.print()
                console.print(f"[cyan]Exporting tasks to: {output_dir}[/]")
                count = export_tasks(session, output_dir)
                if count > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Exported {count} tasks[/]\n\nLocation: {output_dir / 'tasks.csv'}",
                        border_style="green",
                        title="Export Complete"
                    ))

            elif "Export Interactions" in action:
                console.print()
                console.print(f"[cyan]Exporting interactions to: {output_dir}[/]")
                count = export_interactions(session, output_dir)
                if count > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Exported {count} interactions[/]\n\nLocation: {output_dir / 'interactions.csv'}",
                        border_style="green",
                        title="Export Complete"
                    ))

            elif "Export Relationships" in action:
                console.print()
                console.print(f"[cyan]Exporting relationships to: {output_dir}[/]")
                count1 = export_profile_relationships(session, output_dir)
                count2 = export_company_relationships(session, output_dir)
                console.print()
                console.print(Panel(
                    f"[bold green]✓ Export completed![/]\n\nProfile relationships: {count1}\nCompany relationships: {count2}\nLocation: {output_dir}",
                    border_style="green",
                    title="Export Complete"
                ))

            elif "Export Tags" in action:
                console.print()
                console.print(f"[cyan]Exporting tags to: {output_dir}[/]")
                count = export_tags(session, output_dir)
                if count > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Exported {count} tags[/]\n\nLocation: {output_dir / 'tags.csv'}",
                        border_style="green",
                        title="Export Complete"
                    ))

            elif "Export Reminders" in action:
                console.print()
                console.print(f"[cyan]Exporting reminders to: {output_dir}[/]")
                count = export_reminders(session, output_dir)
                if count > 0:
                    console.print()
                    console.print(Panel(
                        f"[bold green]✓ Exported {count} reminders[/]\n\nLocation: {output_dir / 'reminders.csv'}",
                        border_style="green",
                        title="Export Complete"
                    ))

            elif "Export Other Data" in action:
                console.print()
                console.print(f"[cyan]Exporting teams, documents, and activities to: {output_dir}[/]")
                count1 = export_teams(session, output_dir)
                count2 = export_documents(session, output_dir)
                count3 = export_activities(session, output_dir)
                console.print()
                console.print(Panel(
                    f"[bold green]✓ Export completed![/]\n\nTeams: {count1}\nDocuments: {count2}\nActivities: {count3}\nLocation: {output_dir}",
                    border_style="green",
                    title="Export Complete"
                ))

            elif "Back to Dashboard" in action:
                session.close()
                return None

            # Wait for user to continue
            console.print()
            questionary.press_any_key_to_continue("Press any key to continue...").ask()

        except Exception as e:
            console.print()
            console.print(Panel(
                f"[bold red]✗ Export failed![/]\n\n{str(e)}",
                border_style="red",
                title="Export Error"
            ))
            questionary.press_any_key_to_continue("Press any key to continue...").ask()

        # Check for keyboard shortcuts to navigate
        # (Similar pattern to other menus)

    session.close()
    return None


def import_menu():
    """Import menu - Import data from CSV files"""
    from pathlib import Path
    from leadsauce.commands.import_data import (
        import_profiles_from_csv, import_companies_from_csv, import_all_from_csv
    )
    from leadsauce.utils.constants import APP_DIR

    session = get_session()

    while True:
        console.clear()

        # Show top navigation bar
        console.print(render_top_bar("Import"))
        console.print()

        # Action shortcuts top bar
        actions_text = Text()
        actions_text.append("[1] Import All Data", style="bold cyan")
        actions_text.append(" • ", style="dim")
        actions_text.append("[2] Import Profiles", style="green")
        actions_text.append(" • ", style="dim")
        actions_text.append("[3] Import Companies", style="yellow")
        console.print(Panel(actions_text, title="Import Options", border_style="cyan"))
        console.print()

        # Statistics
        try:
            profile_count = session.query(Profile).count()
            company_count = session.query(Company).count()

            stats_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            stats_table.add_column("Entity Type", style="cyan", width=20)
            stats_table.add_column("Current Count", style="green", justify="right", width=15)

            stats_table.add_row("Profiles", str(profile_count))
            stats_table.add_row("Companies", str(company_count))

            console.print(stats_table)
            console.print()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load statistics: {e}[/]")
            console.print()

        # Import instructions
        console.print(Panel(
            "[cyan]Import Instructions:[/]\n\n"
            "• CSV format must match export format\n"
            "• [bold]Bulk mode[/]: Import all records at once\n"
            "• [bold]Separate mode[/]: Confirm each record before importing\n"
            "• Duplicates are skipped by default (by email/name)",
            title="ℹ️  How to Import",
            border_style="cyan"
        ))
        console.print()

        # Create menu choices
        choices = [
            "📦 [1] Import All Data from CSV (profiles + companies)",
            "👥 [2] Import Profiles Only",
            "🏢 [3] Import Companies Only",
            "🔙 Back to Dashboard"
        ]

        action = questionary.select(
            "Select import option:",
            choices=choices,
            style=custom_style
        ).ask()

        if not action:
            return None  # User cancelled (Ctrl+C)

        try:
            if "Back to Dashboard" in action:
                session.close()
                return None

            # Ask for CSV file path
            console.print()
            file_path = questionary.text(
                "Enter path to CSV file:",
                style=custom_style
            ).ask()

            if not file_path:
                console.print("[yellow]Import cancelled[/]")
                questionary.press_any_key_to_continue("Press any key to continue...").ask()
                continue

            csv_path = Path(file_path).expanduser().resolve()

            if not csv_path.exists():
                console.print()
                console.print(Panel(
                    f"[bold red]File not found:[/]\n\n{csv_path}",
                    border_style="red",
                    title="Error"
                ))
                questionary.press_any_key_to_continue("Press any key to continue...").ask()
                continue

            # If it's a directory, try to find CSV files
            if csv_path.is_dir():
                csv_files = list(csv_path.glob('*.csv'))

                if not csv_files:
                    console.print()
                    console.print(Panel(
                        f"[bold red]No CSV files found in directory:[/]\n\n{csv_path}",
                        border_style="red",
                        title="Error"
                    ))
                    questionary.press_any_key_to_continue("Press any key to continue...").ask()
                    continue

                if len(csv_files) == 1:
                    # Only one CSV file, use it automatically
                    csv_path = csv_files[0]
                    console.print(f"[cyan]Found CSV file: {csv_path.name}[/]")
                else:
                    # Multiple CSV files, let user choose
                    console.print()
                    console.print(f"[cyan]Found {len(csv_files)} CSV files in directory[/]")

                    file_choices = [f.name for f in csv_files]
                    file_choices.append("Cancel")

                    selected_file = questionary.select(
                        "Select CSV file to import:",
                        choices=file_choices,
                        style=custom_style
                    ).ask()

                    if not selected_file or selected_file == "Cancel":
                        continue

                    csv_path = csv_path / selected_file


            # Ask for import mode
            mode = questionary.select(
                "Import mode:",
                choices=[
                    "Bulk (import all at once)",
                    "Separate (confirm each record)"
                ],
                style=custom_style
            ).ask()

            if not mode:
                continue

            import_mode = 'bulk' if 'Bulk' in mode else 'separate'

            # Ask about duplicates
            allow_duplicates = questionary.confirm(
                "Allow duplicate records?",
                default=False,
                style=custom_style
            ).ask()

            console.print()
            console.print(f"[cyan]Importing from: {csv_path.name}[/]")
            console.print(f"[cyan]Mode: {import_mode}[/]")
            console.print()

            if "Import All Data" in action:
                # Import all (profiles + companies from single file)
                result = import_all_from_csv(
                    session,
                    csv_path,
                    mode=import_mode,
                    skip_duplicates=not allow_duplicates
                )

                console.print()
                console.print(Panel(
                    f"[bold green]✓ Import completed![/]\n\n"
                    f"Profiles imported: {result['profiles']}\n"
                    f"Companies imported: {result['companies']}\n"
                    f"Skipped (duplicates): {result['skipped']}\n"
                    f"Errors: {len(result['errors'])}",
                    border_style="green",
                    title="Import Complete"
                ))

                if result['errors']:
                    console.print()
                    console.print("[yellow]Errors:[/]")
                    for error in result['errors'][:5]:
                        console.print(f"  [yellow]• {error}[/]")
                    if len(result['errors']) > 5:
                        console.print(f"  [yellow]... and {len(result['errors']) - 5} more[/]")

            elif "Import Profiles" in action:
                # Import profiles
                imported, skipped, errors = import_profiles_from_csv(
                    session,
                    csv_path,
                    mode=import_mode,
                    skip_duplicates=not allow_duplicates
                )

                console.print()
                console.print(Panel(
                    f"[bold green]✓ Import completed![/]\n\n"
                    f"Imported: {imported}\n"
                    f"Skipped (duplicates): {skipped}\n"
                    f"Errors: {len(errors)}",
                    border_style="green",
                    title="Import Complete"
                ))

                if errors:
                    console.print()
                    console.print("[yellow]Errors:[/]")
                    for error in errors[:5]:
                        console.print(f"  [yellow]• {error}[/]")
                    if len(errors) > 5:
                        console.print(f"  [yellow]... and {len(errors) - 5} more[/]")

            elif "Import Companies" in action:
                # Import companies
                imported, skipped, errors = import_companies_from_csv(
                    session,
                    csv_path,
                    mode=import_mode,
                    skip_duplicates=not allow_duplicates
                )

                console.print()
                console.print(Panel(
                    f"[bold green]✓ Import completed![/]\n\n"
                    f"Imported: {imported}\n"
                    f"Skipped (duplicates): {skipped}\n"
                    f"Errors: {len(errors)}",
                    border_style="green",
                    title="Import Complete"
                ))

                if errors:
                    console.print()
                    console.print("[yellow]Errors:[/]")
                    for error in errors[:5]:
                        console.print(f"  [yellow]• {error}[/]")
                    if len(errors) > 5:
                        console.print(f"  [yellow]... and {len(errors) - 5} more[/]")

            # Wait for user to continue
            console.print()
            questionary.press_any_key_to_continue("Press any key to continue...").ask()

        except Exception as e:
            console.print()
            console.print(Panel(
                f"[bold red]✗ Import failed![/]\n\n{str(e)}",
                border_style="red",
                title="Import Error"
            ))
            questionary.press_any_key_to_continue("Press any key to continue...").ask()

    session.close()
    return None
