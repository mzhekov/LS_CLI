"""
Export commands for exporting data to CSV files
"""

import click
import csv
import os
from pathlib import Path
from datetime import datetime
from leadsauce.utils.db import get_session
from leadsauce.utils.formatters import print_success, print_error, print_info
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.task import Task
from leadsauce.models.interaction import Interaction
from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship
from leadsauce.models.tag import Tag
from leadsauce.models.reminder import Reminder
from leadsauce.models.team import Team
from leadsauce.models.document import Document
from leadsauce.models.activity import Activity


@click.group()
def export():
    """Export data to CSV files"""
    pass


def export_profiles(session, output_dir):
    """Export profiles to CSV (matching TUI menu format)"""
    profiles = session.query(Profile).order_by(Profile.name).all()

    if not profiles:
        print_info("No profiles to export")
        return 0

    filepath = output_dir / 'profiles.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Match the columns shown in profiles_menu()
        writer.writerow([
            'ID', 'Name', 'Seniority', 'Email', 'Phone', 'Company',
            'Generation', 'Married', 'Children', 'Skills', 'Tags', 'Notes'
        ])

        for p in profiles:
            # Format exactly like the TUI menu
            company = p.company.name if p.company else '-'
            tags = ', '.join([t.name for t in p.tags]) if p.tags else '-'
            email = p.email if p.email else '-'
            phone = p.phone if p.phone else '-'
            generation = p.generation if p.generation else '-'
            married = '✓' if p.married else '-'
            children = '✓' if p.has_children else '-'
            skills = p.good_at if p.good_at else '-'
            notes = p.notes if p.notes else '-'

            writer.writerow([
                p.id,
                p.name,
                p.seniority.title() if p.seniority else '-',
                email,
                phone,
                company,
                generation,
                married,
                children,
                skills,
                tags,
                notes
            ])

    return len(profiles)


def export_companies(session, output_dir):
    """Export companies to CSV (matching TUI menu format)"""
    companies = session.query(Company).order_by(Company.name).all()

    if not companies:
        print_info("No companies to export")
        return 0

    filepath = output_dir / 'companies.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Match the columns shown in companies_menu()
        writer.writerow([
            'ID', 'Name', 'Industry', 'Size', 'Location', 'Website', 'Profiles', 'Notes'
        ])

        for c in companies:
            # Format exactly like the TUI menu
            industry = c.industry if c.industry else '-'
            size = c.size if c.size else '-'
            location = c.location if c.location else '-'
            website = c.website if c.website else '-'
            profiles_count = len(c.profiles)
            notes = c.notes if c.notes else '-'

            writer.writerow([
                c.id,
                c.name,
                industry,
                size,
                location,
                website,
                profiles_count,
                notes
            ])

    return len(companies)


def export_tasks(session, output_dir):
    """Export tasks to CSV"""
    tasks = session.query(Task).all()

    if not tasks:
        print_info("No tasks to export")
        return 0

    filepath = output_dir / 'tasks.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Title', 'Description', 'Status', 'Priority',
            'Due Date', 'Completed At', 'Linked Profiles', 'Linked Companies',
            'Tags', 'Created At', 'Updated At'
        ])

        for t in tasks:
            writer.writerow([
                t.id,
                t.title,
                t.description or '',
                t.status,
                t.priority,
                t.due_date.isoformat() if t.due_date else '',
                t.completed_at.isoformat() if t.completed_at else '',
                '; '.join([p.name for p in t.profiles]) if t.profiles else '',
                '; '.join([c.name for c in t.companies]) if t.companies else '',
                '; '.join([tag.name for tag in t.tags]) if t.tags else '',
                t.created_at.isoformat() if t.created_at else '',
                t.updated_at.isoformat() if t.updated_at else ''
            ])

    return len(tasks)


def export_interactions(session, output_dir):
    """Export interactions to CSV"""
    interactions = session.query(Interaction).all()

    if not interactions:
        print_info("No interactions to export")
        return 0

    filepath = output_dir / 'interactions.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Profile ID', 'Profile Name', 'Interaction Type',
            'Subject', 'Notes', 'Interaction Date', 'Visibility',
            'Created At', 'Updated At'
        ])

        for i in interactions:
            writer.writerow([
                i.id,
                i.profile_id,
                i.profile.name if i.profile else '',
                i.interaction_type,
                i.subject or '',
                i.notes or '',
                i.interaction_date.isoformat() if i.interaction_date else '',
                i.visibility or '',
                i.created_at.isoformat() if i.created_at else '',
                i.updated_at.isoformat() if i.updated_at else ''
            ])

    return len(interactions)


def export_profile_relationships(session, output_dir):
    """Export profile relationships to CSV"""
    relationships = session.query(ProfileRelationship).all()

    if not relationships:
        print_info("No profile relationships to export")
        return 0

    filepath = output_dir / 'profile_relationships.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'From Profile ID', 'From Profile Name',
            'To Profile ID', 'To Profile Name', 'Relationship Type',
            'Notes', 'Created At'
        ])

        for r in relationships:
            writer.writerow([
                r.id,
                r.from_profile_id,
                r.from_profile.name if r.from_profile else '',
                r.to_profile_id,
                r.to_profile.name if r.to_profile else '',
                r.relationship_type,
                r.notes or '',
                r.created_at.isoformat() if r.created_at else ''
            ])

    return len(relationships)


def export_company_relationships(session, output_dir):
    """Export company relationships to CSV"""
    relationships = session.query(CompanyRelationship).all()

    if not relationships:
        print_info("No company relationships to export")
        return 0

    filepath = output_dir / 'company_relationships.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'From Company ID', 'From Company Name',
            'To Company ID', 'To Company Name', 'Relationship Type',
            'Notes', 'Created At'
        ])

        for r in relationships:
            writer.writerow([
                r.id,
                r.from_company_id,
                r.from_company.name if r.from_company else '',
                r.to_company_id,
                r.to_company.name if r.to_company else '',
                r.relationship_type,
                r.notes or '',
                r.created_at.isoformat() if r.created_at else ''
            ])

    return len(relationships)


def export_tags(session, output_dir):
    """Export tags to CSV"""
    tags = session.query(Tag).all()

    if not tags:
        print_info("No tags to export")
        return 0

    filepath = output_dir / 'tags.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Name', 'Color', 'Description', 'Created At'
        ])

        for t in tags:
            writer.writerow([
                t.id,
                t.name,
                t.color or '',
                t.description or '',
                t.created_at.isoformat() if t.created_at else ''
            ])

    return len(tags)


def export_reminders(session, output_dir):
    """Export reminders to CSV"""
    reminders = session.query(Reminder).all()

    if not reminders:
        print_info("No reminders to export")
        return 0

    filepath = output_dir / 'reminders.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Profile ID', 'Profile Name', 'Title', 'Description',
            'Category', 'Priority', 'Reminder Date', 'Completed',
            'Completed At', 'Created At', 'Updated At'
        ])

        for r in reminders:
            writer.writerow([
                r.id,
                r.profile_id or '',
                r.profile.name if r.profile else '',
                r.title,
                r.description or '',
                r.category or '',
                r.priority or '',
                r.reminder_date.isoformat() if r.reminder_date else '',
                'Yes' if r.completed else 'No',
                r.completed_at.isoformat() if r.completed_at else '',
                r.created_at.isoformat() if r.created_at else '',
                r.updated_at.isoformat() if r.updated_at else ''
            ])

    return len(reminders)


def export_teams(session, output_dir):
    """Export teams to CSV"""
    teams = session.query(Team).all()

    if not teams:
        print_info("No teams to export")
        return 0

    filepath = output_dir / 'teams.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Name', 'Description', 'Member Count', 'Created At', 'Updated At'
        ])

        for t in teams:
            writer.writerow([
                t.id,
                t.name,
                t.description or '',
                len(t.members) if hasattr(t, 'members') else 0,
                t.created_at.isoformat() if t.created_at else '',
                t.updated_at.isoformat() if t.updated_at else ''
            ])

    return len(teams)


def export_documents(session, output_dir):
    """Export document metadata to CSV"""
    documents = session.query(Document).all()

    if not documents:
        print_info("No documents to export")
        return 0

    filepath = output_dir / 'documents.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Profile ID', 'Profile Name', 'Filename', 'File Type',
            'Document Type', 'File Path', 'File Size', 'Created At'
        ])

        for d in documents:
            writer.writerow([
                d.id,
                d.profile_id or '',
                d.profile.name if d.profile else '',
                d.filename,
                d.file_type or '',
                d.document_type or '',
                d.file_path or '',
                d.file_size or '',
                d.created_at.isoformat() if d.created_at else ''
            ])

    return len(documents)


def export_activities(session, output_dir):
    """Export activity log to CSV"""
    activities = session.query(Activity).all()

    if not activities:
        print_info("No activities to export")
        return 0

    filepath = output_dir / 'activities.csv'
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Action', 'Entity Type', 'Entity ID', 'Details', 'Created At'
        ])

        for a in activities:
            writer.writerow([
                a.id,
                a.action,
                a.entity_type or '',
                a.entity_id or '',
                a.details or '',
                a.created_at.isoformat() if a.created_at else ''
            ])

    return len(activities)


@export.command('all')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory for CSV files')
@click.pass_context
def export_all(ctx, output_dir):
    """Export all data to CSV files

    This will create separate CSV files for each data type:
    - profiles.csv
    - companies.csv
    - tasks.csv
    - interactions.csv
    - profile_relationships.csv
    - company_relationships.csv
    - tags.csv
    - reminders.csv
    - teams.csv
    - documents.csv
    - activities.csv

    Example:
        leadsauce export all
        leadsauce export all --output-dir ~/exports
    """

    try:
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir).expanduser().resolve()
        else:
            # Use ~/.leadsauce/exports/ as default
            from leadsauce.utils.constants import APP_DIR
            output_path = APP_DIR / 'exports' / datetime.now().strftime('%Y%m%d_%H%M%S')

        output_path.mkdir(parents=True, exist_ok=True)

        click.echo(f"Exporting all data to: {output_path}")
        click.echo()

        session = get_session()

        # Export each entity type
        exporters = [
            ('Profiles', export_profiles),
            ('Companies', export_companies),
            ('Tasks', export_tasks),
            ('Interactions', export_interactions),
            ('Profile Relationships', export_profile_relationships),
            ('Company Relationships', export_company_relationships),
            ('Tags', export_tags),
            ('Reminders', export_reminders),
            ('Teams', export_teams),
            ('Documents', export_documents),
            ('Activities', export_activities)
        ]

        total_exported = 0
        for name, exporter_func in exporters:
            try:
                count = exporter_func(session, output_path)
                if count > 0:
                    click.secho(f"✓ Exported {count} {name}", fg='green')
                    total_exported += count
            except Exception as e:
                click.secho(f"✗ Failed to export {name}: {str(e)}", fg='yellow')

        click.echo()
        print_success(f"Export completed! Total records exported: {total_exported}")
        click.echo(f"Files saved to: {output_path}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@export.command('profiles')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def export_profiles_only(ctx, output):
    """Export profiles to CSV file"""

    try:
        session = get_session()

        if output:
            output_path = Path(output).expanduser().resolve()
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            from leadsauce.utils.constants import APP_DIR
            output_dir = APP_DIR / 'exports'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'profiles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        # Temporarily change output to match expected structure
        temp_dir = output_path.parent
        count = export_profiles(session, temp_dir)

        # Rename if needed
        if output:
            generated_file = temp_dir / 'profiles.csv'
            if generated_file.exists() and generated_file != output_path:
                generated_file.rename(output_path)
        else:
            output_path = temp_dir / 'profiles.csv'

        if count > 0:
            print_success(f"Exported {count} profiles to {output_path}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@export.command('companies')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def export_companies_only(ctx, output):
    """Export companies to CSV file"""

    try:
        session = get_session()

        if output:
            output_path = Path(output).expanduser().resolve()
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            from leadsauce.utils.constants import APP_DIR
            output_dir = APP_DIR / 'exports'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'companies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        temp_dir = output_path.parent
        count = export_companies(session, temp_dir)

        if output:
            generated_file = temp_dir / 'companies.csv'
            if generated_file.exists() and generated_file != output_path:
                generated_file.rename(output_path)
        else:
            output_path = temp_dir / 'companies.csv'

        if count > 0:
            print_success(f"Exported {count} companies to {output_path}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@export.command('tasks')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def export_tasks_only(ctx, output):
    """Export tasks to CSV file"""

    try:
        session = get_session()

        if output:
            output_path = Path(output).expanduser().resolve()
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            from leadsauce.utils.constants import APP_DIR
            output_dir = APP_DIR / 'exports'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'tasks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        temp_dir = output_path.parent
        count = export_tasks(session, temp_dir)

        if output:
            generated_file = temp_dir / 'tasks.csv'
            if generated_file.exists() and generated_file != output_path:
                generated_file.rename(output_path)
        else:
            output_path = temp_dir / 'tasks.csv'

        if count > 0:
            print_success(f"Exported {count} tasks to {output_path}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()
