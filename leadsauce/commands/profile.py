"""
Profile management commands
"""

import click
import json
import logging
from datetime import datetime
from tabulate import tabulate
from sqlalchemy import or_
from leadsauce.utils.db import get_session
from leadsauce.utils.validators import validate_email, validate_phone, parse_tags
from leadsauce.utils.formatters import print_success, print_error, print_info, format_date
from leadsauce.utils.constants import SENIORITY_LEVELS, GENERATION_TYPES
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag
from leadsauce.models.associations import profile_tags

logger = logging.getLogger('leadsauce.commands.profile')


@click.group()
def profile():
    """Profile management commands"""
    pass


@profile.command('create')
@click.option('--name', required=True, help='Contact name')
@click.option('--seniority', required=True, type=click.Choice(SENIORITY_LEVELS, case_sensitive=False), help='Seniority level')
@click.option('--company', help='Company name or ID')
@click.option('--email', help='Email address')
@click.option('--phone', help='Phone number')
@click.option('--generation', type=click.Choice(GENERATION_TYPES, case_sensitive=False), help='Generation')
@click.option('--married', is_flag=True, help='Married status')
@click.option('--has-children', is_flag=True, help='Has children')
@click.option('--skills', help='Comma-separated skills (good_at)')
@click.option('--tags', help='Comma-separated tags')
@click.option('--notes', help='Additional notes')
@click.option('--interactive', is_flag=True, help='Interactive mode')

@click.pass_context
def create_profile(ctx, name, seniority, company, email, phone, generation, married, has_children, skills, tags, notes, interactive):
    """Create a new profile"""

    if interactive:
        # Interactive prompts
        name = click.prompt('Name', default=name if name else '')
        seniority = click.prompt('Seniority', type=click.Choice(SENIORITY_LEVELS), default=seniority if seniority else 'mid')
        company = click.prompt('Company (optional)', default=company if company else '', show_default=False)
        email = click.prompt('Email (optional)', default=email if email else '', show_default=False)
        phone = click.prompt('Phone (optional)', default=phone if phone else '', show_default=False)
        generation = click.prompt('Generation (optional)', type=click.Choice(GENERATION_TYPES + ['']), default='', show_default=False) or None
        married = click.confirm('Married?', default=married)
        has_children = click.confirm('Has children?', default=has_children)
        skills = click.prompt('Skills (comma-separated, optional)', default=skills if skills else '', show_default=False)
        tags = click.prompt('Tags (comma-separated, optional)', default=tags if tags else '', show_default=False)
        notes = click.prompt('Notes (optional)', default=notes if notes else '', show_default=False)

    # Validate email if provided
    if email and not validate_email(email):
        print_error("Invalid email address")
        raise click.Abort()

    # Validate phone if provided
    if phone and not validate_phone(phone):
        print_error("Invalid phone number")
        raise click.Abort()

    logger.debug(f"Creating profile: {name}, seniority: {seniority}")

    try:
        session = get_session()

        # Handle company
        company_id = None
        if company:
            logger.debug(f"Looking up company: {company}")
            # Try to find existing company by ID or name
            if company.isdigit():
                company_obj = session.query(Company).filter(
                    Company.id == int(company),
                    1==1
                ).first()
            else:
                company_obj = session.query(Company).filter(
                    Company.name.ilike(f"%{company}%"),
                    1==1
                ).first()

            if company_obj:
                company_id = company_obj.id
                logger.debug(f"Found existing company: {company_obj.name} (ID: {company_id})")
                click.echo(f"Using existing company: {company_obj.name}")
            else:
                # Create new company
                if click.confirm(f"Company '{company}' not found. Create it?", default=True):
                    new_company = Company(

                        name=company
                    )
                    session.add(new_company)
                    session.flush()
                    company_id = new_company.id
                    logger.info(f"Created new company: {company} (ID: {company_id})")
                    click.echo(f"Created new company: {company}")

        # Create profile
        new_profile = Profile(

            company_id=company_id,
            name=name,
            email=email or None,
            phone=phone or None,
            seniority=seniority.lower(),
            generation=generation.lower() if generation else None,
            married=married,
            has_children=has_children,
            good_at=skills or None,
            notes=notes or None
        )

        session.add(new_profile)
        session.flush()
        logger.debug(f"Profile {name} added to session (ID: {new_profile.id})")

        # Handle tags
        if tags:
            tag_names = parse_tags(tags)
            logger.debug(f"Processing {len(tag_names)} tags: {tag_names}")
            for tag_name in tag_names:
                # Find or create tag
                tag = session.query(Tag).filter(
                    1==1,
                    Tag.name == tag_name
                ).first()

                if not tag:
                    tag = Tag( name=tag_name)
                    session.add(tag)
                    session.flush()
                    logger.debug(f"Created new tag: {tag_name}")

                new_profile.tags.append(tag)

        session.commit()
        logger.info(f"Profile created successfully: {name} (ID: {new_profile.id})")

        print_success(f"Profile created successfully (ID: {new_profile.id})")
        click.echo(f"Name: {new_profile.name}")
        click.echo(f"Seniority: {new_profile.seniority}")
        if company_id:
            click.echo(f"Company: {new_profile.company.name}")
        if new_profile.tags:
            click.echo(f"Tags: {', '.join([t.name for t in new_profile.tags])}")

    except Exception as e:
        logger.error(f"Failed to create profile {name}: {str(e)}", exc_info=True)
        print_error(f"Failed to create profile: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@profile.command('list')
@click.option('--limit', default=50, help='Number of results')
@click.option('--offset', default=0, help='Offset for pagination')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.option('--filter', 'filters', multiple=True, help='Filters (key=value)')
@click.option('--tags', help='Filter by tags (comma-separated)')
@click.option('--company', help='Filter by company')
@click.option('--seniority', type=click.Choice(SENIORITY_LEVELS, case_sensitive=False), help='Filter by seniority')
@click.option('--sort-by', default='name', help='Sort field')

@click.pass_context
def list_profiles(ctx, limit, offset, output_format, filters, tags, company, seniority, sort_by):
    """List profiles"""

    try:
        session = get_session()

        query = session.query(Profile).filter(1==1)

        # Apply seniority filter
        if seniority:
            query = query.filter(Profile.seniority == seniority.lower())

        # Apply company filter
        if company:
            if company.isdigit():
                query = query.filter(Profile.company_id == int(company))
            else:
                query = query.join(Company).filter(Company.name.ilike(f"%{company}%"))

        # Apply tag filter
        if tags:
            tag_names = parse_tags(tags)
            query = query.join(Profile.tags).filter(Tag.name.in_(tag_names))

        # Apply custom filters
        for filter_str in filters:
            try:
                key, value = filter_str.split('=', 1)
                if hasattr(Profile, key):
                    query = query.filter(getattr(Profile, key) == value)
            except ValueError:
                print_error(f"Invalid filter format: '{filter_str}'. Use 'key=value'")
                continue

        # Apply sorting
        if hasattr(Profile, sort_by):
            query = query.order_by(getattr(Profile, sort_by))

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        profiles = query.limit(limit).offset(offset).all()

        # Format output
        if output_format == 'json':
            output = [p.to_dict(include_relations=True) for p in profiles]
            click.echo(json.dumps(output, indent=2, default=str))

        elif output_format == 'csv':
            import csv
            import sys
            writer = csv.writer(sys.stdout)
            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Seniority', 'Company', 'Last Contact', 'Tags'])
            for p in profiles:
                writer.writerow([
                    p.id,
                    p.name,
                    p.email or '',
                    p.phone or '',
                    p.seniority,
                    p.company.name if p.company else '',
                    format_date(p.last_contact) if p.last_contact else 'Never',
                    ', '.join([t.name for t in p.tags[:3]]) if p.tags else ''
                ])

        else:  # table
            headers = ['ID', 'Name', 'Seniority', 'Company', 'Last Contact', 'Tags']
            rows = []
            for p in profiles:
                rows.append([
                    p.id,
                    p.name[:30],
                    p.seniority,
                    (p.company.name[:20] if p.company else '-'),
                    format_date(p.last_contact) if p.last_contact else 'Never',
                    ', '.join([t.name for t in p.tags[:2]]) if p.tags else '-'
                ])

            if rows:
                click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
                click.echo(f"\nShowing {len(profiles)} of {total_count} profiles (offset: {offset})")
            else:
                print_info("No profiles found")

                if filters or tags or company or seniority:
                    click.echo("Try adjusting your filters")

    except Exception as e:
        print_error(f"Failed to list profiles: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@profile.command('show')
@click.argument('profile_id', type=int)
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='Output format')

@click.pass_context
def show_profile(ctx, profile_id, output_format):
    """Show profile details"""

    try:
        session = get_session()

        profile = session.query(Profile).filter(
            Profile.id == profile_id,
            1==1
        ).first()

        if not profile:
            print_error(f"Profile not found")
            raise click.Abort()

        if output_format == 'json':
            click.echo(json.dumps(profile.to_dict(include_relations=True), indent=2, default=str))
        else:
            # Text format
            click.echo()
            click.secho(f"{profile.name}", fg='cyan', bold=True)
            click.echo('=' * 70)
            click.echo(f"ID:                {profile.id}")
            click.echo(f"Email:             {profile.email or 'N/A'}")
            click.echo(f"Phone:             {profile.phone or 'N/A'}")
            click.echo(f"Seniority:         {profile.seniority}")
            if profile.generation:
                click.echo(f"Generation:        {profile.generation}")
            click.echo(f"Company:           {profile.company.name if profile.company else 'N/A'}")
            click.echo(f"Married:           {'Yes' if profile.married else 'No'}")
            click.echo(f"Has Children:      {'Yes' if profile.has_children else 'No'}")
            click.echo(f"Last Contact:      {format_date(profile.last_contact) if profile.last_contact else 'Never'}")
            click.echo(f"Interactions:      {profile.interaction_count}")
            click.echo(f"Tags:              {', '.join([t.name for t in profile.tags]) if profile.tags else 'None'}")
            click.echo(f"Created:           {format_date(profile.created_at)}")

            if profile.good_at:
                click.echo(f"\nSkills:            {profile.good_at}")

            if profile.notes:
                click.echo(f"\nNotes:")
                click.echo(f"{profile.notes}")

            # Show recent interactions
            if profile.interactions:
                click.echo(f"\nRecent Interactions:")
                for i in profile.interactions[:5]:
                    click.echo(f"  • [{i.interaction_type}] {i.subject or 'No subject'} - {format_date(i.interaction_date)}")

            # Show active reminders
            active_reminders = [r for r in profile.reminders if not r.completed]
            if active_reminders:
                click.echo(f"\nActive Reminders:")
                for r in active_reminders[:5]:
                    priority_color = {'high': 'red', 'medium': 'yellow', 'low': 'green'}
                    click.secho(f"  • [{r.priority}] {r.title} - Due: {format_date(r.reminder_date)}",
                               fg=priority_color.get(r.priority, 'white'))

            click.echo()

    except Exception as e:
        print_error(f"Failed to show profile: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@profile.command('delete')
@click.argument('profile_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation')

@click.pass_context
def delete_profile(ctx, profile_id, force):
    """Delete a profile"""

    try:
        session = get_session()

        profile = session.query(Profile).filter(
            Profile.id == profile_id,
            1==1
        ).first()

        if not profile:
            print_error(f"Profile not found")
            raise click.Abort()

        # Confirmation
        if not force:
            if not click.confirm(f"Delete profile '{profile.name}'? This will also delete all interactions, reminders, and documents."):
                click.echo("Operation cancelled")
                raise click.Abort()

        name = profile.name
        session.delete(profile)
        session.commit()

        print_success(f"Profile '{name}' deleted successfully")

    except Exception as e:
        print_error(f"Failed to delete profile: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@profile.command('search')
@click.argument('query')
@click.option('--fields', default='name,email,good_at', help='Fields to search (comma-separated)')
@click.option('--limit', default=20, help='Number of results')

@click.pass_context
def search_profiles(ctx, query, fields, limit):
    """Search profiles"""

    try:
        session = get_session()

        field_list = [f.strip() for f in fields.split(',')]

        # Build search query
        filters = []
        for field in field_list:
            if hasattr(Profile, field):
                filters.append(getattr(Profile, field).ilike(f"%{query}%"))

        if not filters:
            print_error("No valid fields specified")
            raise click.Abort()

        profiles = session.query(Profile).filter(
            1==1,
            or_(*filters)
        ).limit(limit).all()

        if not profiles:
            print_info(f"No profiles found matching '{query}'")
        else:
            headers = ['ID', 'Name', 'Email', 'Seniority', 'Company']
            rows = []
            for p in profiles:
                rows.append([
                    p.id,
                    p.name[:30],
                    p.email[:30] if p.email else '-',
                    p.seniority,
                    (p.company.name[:20] if p.company else '-')
                ])

            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            click.echo(f"\nFound {len(profiles)} matching profiles")

    except Exception as e:
        print_error(f"Search failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()
