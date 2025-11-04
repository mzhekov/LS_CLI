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

# Navigation menu items
NAV_ITEMS = [
    ("Dashboard", "📊"),
    ("Profiles", "👥"),
    ("Companies", "🏢"),
    ("Network Map", "🗺️"),
    ("Search", "🔍"),
    ("Tags", "🏷️"),
    ("Exit", "❌")
]


def render_top_bar(current_view="Dashboard"):
    """Render the top navigation bar"""
    nav_text = Text()

    for i, (name, icon) in enumerate(NAV_ITEMS):
        if i > 0:
            nav_text.append(" │ ", style="dim")

        if name == current_view:
            nav_text.append(f"{icon} {name}", style="bold cyan on #1a1a1a")
        else:
            nav_text.append(f"{icon} {name}", style="white")

    return Panel(nav_text, style="cyan", box=box.SIMPLE)


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
            browse_profiles()
            current_view = "Dashboard"  # Return to dashboard after
            continue
        elif current_view == "Companies":
            browse_companies()
            current_view = "Dashboard"
            continue
        elif current_view == "Network Map":
            show_network_map()
        elif current_view == "Search":
            search_interactive()
            current_view = "Dashboard"
            continue
        elif current_view == "Tags":
            manage_tags()
            current_view = "Dashboard"
            continue
        elif current_view == "Exit":
            console.print("\n[cyan]Goodbye! 👋[/]\n")
            break

        # Navigation menu at bottom
        console.print()
        nav_choices = [f"{icon} {name}" for name, icon in NAV_ITEMS]

        action = questionary.select(
            "Navigate to:",
            choices=nav_choices,
            style=custom_style
        ).ask()

        if not action:
            break

        # Extract view name from selection
        for name, icon in NAV_ITEMS:
            if action == f"{icon} {name}":
                current_view = name
                break


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
            "[yellow]No profiles yet. Navigate to Profiles to add your first contact![/]",
            border_style="yellow"
        ))

    session.close()


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
    """Manage tags interactively"""
    session = get_session()

    while True:
        console.clear()
        tags = session.query(Tag).order_by(Tag.name).all()

        console.print(Panel(
            f"[bold cyan]Tags ({len(tags)} total)[/]",
            border_style="cyan"
        ))
        console.print()

        if tags:
            for tag in tags:
                count = len(tag.profiles)
                color = tag.color or "white"
                console.print(f"  • [{color}]{tag.name}[/] ({count} profiles)")
        else:
            console.print("[yellow]No tags found[/]")

        console.print()
        questionary.press_any_key_to_continue("Press any key to go back...").ask()
        break

    session.close()
