"""
Interactive TUI for LeadSauce CLI with top bar navigation
"""

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
    ("Network Map", "🗺️", "4"),
    ("Search", "🔍", "5"),
    ("Tags", "🏷️", "6"),
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
        console.print("[dim]You can either:[/]")
        console.print("[dim]  • Type a number (1-6) or 'q' to quit[/]")
        console.print("[dim]  • Press Enter to use arrow keys[/]")
        console.print()

        # Create a simple text prompt that accepts keyboard shortcuts
        nav_input = questionary.text(
            "Quick nav:",
            style=custom_style,
            default=""
        ).ask()

        if not nav_input:
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
    """Show profiles action menu"""
    while True:
        console.clear()
        console.print(Panel(
            "[bold cyan]👥 Profiles Management[/]\n"
            "[dim]Choose an action[/]",
            border_style="cyan"
        ))
        console.print()

        choices = [
            "📋 Browse All Profiles",
            "➕ Add New Profile",
            "🔍 Search Profiles",
            "← Back to Dashboard"
        ]

        action = questionary.select(
            "What would you like to do?",
            choices=choices,
            style=custom_style
        ).ask()

        if not action or action == "← Back to Dashboard":
            break
        elif action == "📋 Browse All Profiles":
            browse_profiles()
        elif action == "➕ Add New Profile":
            add_profile_interactive()
        elif action == "🔍 Search Profiles":
            search_interactive()


def companies_menu():
    """Show companies action menu"""
    while True:
        console.clear()
        console.print(Panel(
            "[bold cyan]🏢 Companies Management[/]\n"
            "[dim]Choose an action[/]",
            border_style="cyan"
        ))
        console.print()

        choices = [
            "📋 Browse All Companies",
            "➕ Add New Company",
            "✏️  Edit Company",
            "← Back to Dashboard"
        ]

        action = questionary.select(
            "What would you like to do?",
            choices=choices,
            style=custom_style
        ).ask()

        if not action or action == "← Back to Dashboard":
            break
        elif action == "📋 Browse All Companies":
            browse_companies()
        elif action == "➕ Add New Company":
            add_company_interactive()
        elif action == "✏️  Edit Company":
            edit_company_menu()


def tags_menu():
    """Show tags action menu"""
    while True:
        console.clear()
        console.print(Panel(
            "[bold cyan]🏷️  Tags Management[/]\n"
            "[dim]Choose an action[/]",
            border_style="cyan"
        ))
        console.print()

        choices = [
            "📋 View All Tags",
            "➕ Add New Tag",
            "✏️  Edit Tag",
            "🗑️  Delete Tag",
            "← Back to Dashboard"
        ]

        action = questionary.select(
            "What would you like to do?",
            choices=choices,
            style=custom_style
        ).ask()

        if not action or action == "← Back to Dashboard":
            break
        elif action == "📋 View All Tags":
            view_tags_detailed()
        elif action == "➕ Add New Tag":
            add_tag_interactive()
        elif action == "✏️  Edit Tag":
            edit_tag_interactive()
        elif action == "🗑️  Delete Tag":
            delete_tag_interactive()


def show_network_map():
    """Show relationship map between profiles"""
    session = get_session()

    profiles = session.query(Profile).all()

    if not profiles:
        console.print(Panel(
            "[yellow]No profiles to map. Add some profiles first![/]",
            border_style="yellow"
        ))
        questionary.press_any_key_to_continue("Press any key to continue...").ask()
        session.close()
        return

    # Build relationship data
    company_groups = defaultdict(list)
    tag_connections = defaultdict(set)

    for profile in profiles:
        # Group by company
        if profile.company:
            company_groups[profile.company.name].append(profile)

        # Track tag connections
        for tag in profile.tags:
            tag_connections[tag.name].add(profile.id)

    # Display network map
    console.print(Panel(
        "[bold cyan]Network Relationship Map[/]\n"
        "[dim]Showing connections by company and shared tags[/]",
        border_style="cyan"
    ))
    console.print()

    # Company-based connections
    if company_groups:
        console.print("[bold yellow]📊 By Company:[/]\n")

        for company_name, company_profiles in sorted(company_groups.items()):
            if len(company_profiles) > 1:
                # Create visual connection
                console.print(f"  [cyan]🏢 {company_name}[/]")

                for i, profile in enumerate(company_profiles):
                    connector = "├──" if i < len(company_profiles) - 1 else "└──"
                    tags_str = ", ".join([t.name for t in profile.tags[:2]]) if profile.tags else "no tags"
                    console.print(f"    {connector} [white]{profile.name}[/] [dim]({profile.seniority}, {tags_str})[/]")

                console.print()

    # Tag-based connections
    console.print("[bold yellow]🏷️  By Shared Tags:[/]\n")

    strong_connections = []
    for tag_name, profile_ids in tag_connections.items():
        if len(profile_ids) > 1:
            tag_profiles = [p for p in profiles if p.id in profile_ids]
            strong_connections.append((tag_name, tag_profiles))

    if strong_connections:
        # Show top connections
        strong_connections.sort(key=lambda x: len(x[1]), reverse=True)

        for tag_name, tag_profiles in strong_connections[:5]:  # Show top 5
            console.print(f"  [green]🏷️  {tag_name}[/] ({len(tag_profiles)} profiles)")

            for i, profile in enumerate(tag_profiles[:4]):  # Show first 4
                connector = "├──" if i < min(len(tag_profiles), 4) - 1 else "└──"
                company_str = f"@ {profile.company.name}" if profile.company else "no company"
                console.print(f"    {connector} [white]{profile.name}[/] [dim]({company_str})[/]")

            if len(tag_profiles) > 4:
                console.print(f"    └── [dim]... and {len(tag_profiles) - 4} more[/]")

            console.print()
    else:
        console.print("  [dim]No shared tags between profiles yet[/]\n")

    # Network statistics
    console.print()
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan bold", justify="right")
    stats_table.add_column(style="white")

    stats_table.add_row("Total Profiles:", str(len(profiles)))
    stats_table.add_row("Companies:", str(len(company_groups)))
    stats_table.add_row("Shared Tags:", str(len([c for c in strong_connections if len(c[1]) > 1])))

    # Calculate connectivity
    connected_profiles = set()
    for _, tag_profiles in strong_connections:
        for p in tag_profiles:
            connected_profiles.add(p.id)

    connectivity = len(connected_profiles) / len(profiles) * 100 if profiles else 0
    stats_table.add_row("Connectivity:", f"{connectivity:.0f}%")

    console.print(Panel(stats_table, title="[bold yellow]Network Stats[/]", border_style="yellow"))

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
    """Edit profile interactively"""
    console.clear()
    console.print(Panel(
        f"[bold cyan]Edit Profile: {profile.name}[/]",
        border_style="cyan"
    ))
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
        "← Cancel"
    ]

    field = questionary.select(
        "What would you like to edit?",
        choices=fields,
        style=custom_style
    ).ask()

    if not field or field == "← Cancel":
        return

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

    session.commit()
    console.print(f"\n[green]✓ Updated {profile.name}[/]\n")
    questionary.press_any_key_to_continue().ask()


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
    """Edit a company interactively"""
    console.clear()
    console.print(Panel(
        f"[bold cyan]Edit Company: {company.name}[/]",
        border_style="cyan"
    ))
    console.print()

    fields = [
        "Name",
        "Industry",
        "Size",
        "Location",
        "Website",
        "← Cancel"
    ]

    field = questionary.select(
        "What would you like to edit?",
        choices=fields,
        style=custom_style
    ).ask()

    if not field or field == "← Cancel":
        return

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

    session.commit()
    console.print(f"\n[green]✓ Updated {company.name}[/]\n")
    questionary.press_any_key_to_continue().ask()


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
