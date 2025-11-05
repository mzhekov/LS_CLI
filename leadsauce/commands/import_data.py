"""
Import commands for importing data from CSV files
"""

import click
import csv
from pathlib import Path
from leadsauce.utils.db import get_session
from leadsauce.utils.formatters import print_success, print_error, print_info
from leadsauce.utils.validators import validate_email, validate_phone
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag


@click.group(name='import')
def import_cmd():
    """Import data from CSV files"""
    pass


def import_profiles_from_csv(session, csv_path, mode='bulk', skip_duplicates=True):
    """
    Import profiles from CSV file

    Args:
        session: Database session
        csv_path: Path to CSV file
        mode: 'bulk' (import all) or 'separate' (ask for confirmation for each)
        skip_duplicates: Skip profiles with duplicate emails

    Returns:
        tuple: (imported_count, skipped_count, errors)
    """
    imported = 0
    skipped = 0
    errors = []

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # start at 2 (header is 1)
                try:
                    # Extract data from row
                    name = row.get('Name', '').strip()
                    email = row.get('Email', '').strip()
                    phone = row.get('Phone', '').strip()
                    seniority = row.get('Seniority', '').strip().lower()
                    company_name = row.get('Company', '').strip()
                    generation = row.get('Generation', '').strip().lower()
                    married = row.get('Married', '').strip() == '✓'
                    children = row.get('Children', '').strip() == '✓'
                    skills = row.get('Skills', '').strip()
                    tags_str = row.get('Tags', '').strip()
                    notes = row.get('Notes', '').strip()

                    # Validate required fields
                    if not name:
                        errors.append(f"Row {row_num}: Name is required")
                        continue

                    # Convert empty strings and '-' to None
                    email = email if email and email != '-' else None
                    phone = phone if phone and phone != '-' else None
                    generation = generation if generation and generation != '-' else None
                    skills = skills if skills and skills != '-' else None
                    notes = notes if notes and notes != '-' else None

                    # Validate email
                    if email and not validate_email(email):
                        errors.append(f"Row {row_num}: Invalid email '{email}'")
                        continue

                    # Check for duplicates
                    if skip_duplicates and email:
                        existing = session.query(Profile).filter(Profile.email == email).first()
                        if existing:
                            skipped += 1
                            continue

                    # Validate phone
                    if phone and not validate_phone(phone):
                        errors.append(f"Row {row_num}: Invalid phone '{phone}'")
                        continue

                    # Find or create company
                    company_id = None
                    if company_name and company_name != '-':
                        company = session.query(Company).filter(
                            Company.name.ilike(company_name)
                        ).first()

                        if not company:
                            company = Company(name=company_name)
                            session.add(company)
                            session.flush()

                        company_id = company.id

                    # In separate mode, ask for confirmation
                    if mode == 'separate':
                        click.echo(f"\nImport profile: {name} ({email or 'no email'})?")
                        if not click.confirm("Add this profile?", default=True):
                            skipped += 1
                            continue

                    # Create profile
                    profile = Profile(
                        name=name,
                        email=email,
                        phone=phone,
                        seniority=seniority if seniority else 'mid',
                        company_id=company_id,
                        generation=generation,
                        married=married,
                        has_children=children,
                        good_at=skills,
                        notes=notes
                    )

                    session.add(profile)
                    session.flush()

                    # Handle tags
                    if tags_str and tags_str != '-':
                        tag_names = [t.strip() for t in tags_str.split(',')]
                        for tag_name in tag_names:
                            if tag_name:
                                tag = session.query(Tag).filter(Tag.name == tag_name).first()
                                if not tag:
                                    tag = Tag(name=tag_name)
                                    session.add(tag)
                                    session.flush()
                                profile.tags.append(tag)

                    imported += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue

        # Commit all changes
        if mode == 'bulk':
            session.commit()

        return imported, skipped, errors

    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to read CSV file: {str(e)}")


def import_companies_from_csv(session, csv_path, mode='bulk', skip_duplicates=True):
    """
    Import companies from CSV file

    Args:
        session: Database session
        csv_path: Path to CSV file
        mode: 'bulk' (import all) or 'separate' (ask for confirmation for each)
        skip_duplicates: Skip companies with duplicate names

    Returns:
        tuple: (imported_count, skipped_count, errors)
    """
    imported = 0
    skipped = 0
    errors = []

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Extract data from row
                    name = row.get('Name', '').strip()
                    industry = row.get('Industry', '').strip()
                    size = row.get('Size', '').strip()
                    location = row.get('Location', '').strip()
                    website = row.get('Website', '').strip()
                    notes = row.get('Notes', '').strip()

                    # Validate required fields
                    if not name:
                        errors.append(f"Row {row_num}: Name is required")
                        continue

                    # Convert empty strings and '-' to None
                    industry = industry if industry and industry != '-' else None
                    size = size if size and size != '-' else None
                    location = location if location and location != '-' else None
                    website = website if website and website != '-' else None
                    notes = notes if notes and notes != '-' else None

                    # Check for duplicates
                    if skip_duplicates:
                        existing = session.query(Company).filter(
                            Company.name.ilike(name)
                        ).first()
                        if existing:
                            skipped += 1
                            continue

                    # In separate mode, ask for confirmation
                    if mode == 'separate':
                        click.echo(f"\nImport company: {name} ({industry or 'no industry'})?")
                        if not click.confirm("Add this company?", default=True):
                            skipped += 1
                            continue

                    # Create company
                    company = Company(
                        name=name,
                        industry=industry,
                        size=size,
                        location=location,
                        website=website,
                        notes=notes
                    )

                    session.add(company)
                    imported += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue

        # Commit all changes
        if mode == 'bulk':
            session.commit()

        return imported, skipped, errors

    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to read CSV file: {str(e)}")


def import_all_from_csv(session, csv_path, mode='bulk', skip_duplicates=True):
    """
    Import all data from a single CSV file (exported with 'export all')

    Args:
        session: Database session
        csv_path: Path to CSV file with Type column
        mode: 'bulk' or 'separate'
        skip_duplicates: Skip duplicate records

    Returns:
        dict: Statistics of import
    """
    imported_profiles = 0
    imported_companies = 0
    skipped = 0
    errors = []

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                try:
                    record_type = row.get('Type', '').strip()

                    if record_type == 'Profile':
                        # Import as profile
                        name = row.get('Name', '').strip()
                        email = row.get('Email', '').strip()
                        phone = row.get('Phone', '').strip()
                        seniority = row.get('Seniority', '').strip().lower()
                        company_name = row.get('Company/Industry', '').strip()
                        generation = row.get('Generation', '').strip().lower()
                        married = row.get('Married', '').strip() == '✓'
                        children = row.get('Children', '').strip() == '✓'
                        skills = row.get('Skills', '').strip()
                        tags_str = row.get('Tags', '').strip()
                        notes = row.get('Notes', '').strip()

                        if not name:
                            errors.append(f"Row {row_num}: Profile name is required")
                            continue

                        # Convert empties to None
                        email = email if email and email != '-' else None
                        phone = phone if phone and phone != '-' else None
                        generation = generation if generation and generation != '-' else None
                        skills = skills if skills and skills != '-' else None
                        notes = notes if notes and notes != '-' else None

                        # Check duplicates
                        if skip_duplicates and email:
                            existing = session.query(Profile).filter(Profile.email == email).first()
                            if existing:
                                skipped += 1
                                continue

                        # Find/create company
                        company_id = None
                        if company_name and company_name != '-':
                            company = session.query(Company).filter(
                                Company.name.ilike(company_name)
                            ).first()
                            if not company:
                                company = Company(name=company_name)
                                session.add(company)
                                session.flush()
                            company_id = company.id

                        # In separate mode, ask confirmation
                        if mode == 'separate':
                            click.echo(f"\nImport profile: {name}?")
                            if not click.confirm("Add?", default=True):
                                skipped += 1
                                continue

                        # Create profile
                        profile = Profile(
                            name=name,
                            email=email,
                            phone=phone,
                            seniority=seniority if seniority else 'mid',
                            company_id=company_id,
                            generation=generation,
                            married=married,
                            has_children=children,
                            good_at=skills,
                            notes=notes
                        )
                        session.add(profile)
                        session.flush()

                        # Handle tags
                        if tags_str and tags_str != '-':
                            tag_names = [t.strip() for t in tags_str.split(',')]
                            for tag_name in tag_names:
                                if tag_name:
                                    tag = session.query(Tag).filter(Tag.name == tag_name).first()
                                    if not tag:
                                        tag = Tag(name=tag_name)
                                        session.add(tag)
                                        session.flush()
                                    profile.tags.append(tag)

                        imported_profiles += 1

                    elif record_type == 'Company':
                        # Import as company
                        name = row.get('Name', '').strip()
                        industry = row.get('Company/Industry', '').strip()
                        size = row.get('Size', '').strip()
                        location = row.get('Location', '').strip()
                        website = row.get('Website', '').strip()
                        notes = row.get('Notes', '').strip()

                        if not name:
                            errors.append(f"Row {row_num}: Company name is required")
                            continue

                        # Convert empties to None
                        industry = industry if industry and industry != '-' else None
                        size = size if size and size != '-' else None
                        location = location if location and location != '-' else None
                        website = website if website and website != '-' else None
                        notes = notes if notes and notes != '-' else None

                        # Check duplicates
                        if skip_duplicates:
                            existing = session.query(Company).filter(
                                Company.name.ilike(name)
                            ).first()
                            if existing:
                                skipped += 1
                                continue

                        # In separate mode, ask confirmation
                        if mode == 'separate':
                            click.echo(f"\nImport company: {name}?")
                            if not click.confirm("Add?", default=True):
                                skipped += 1
                                continue

                        # Create company
                        company = Company(
                            name=name,
                            industry=industry,
                            size=size,
                            location=location,
                            website=website,
                            notes=notes
                        )
                        session.add(company)
                        imported_companies += 1

                    else:
                        errors.append(f"Row {row_num}: Unknown type '{record_type}'")

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue

        # Commit all changes
        if mode == 'bulk':
            session.commit()

        return {
            'profiles': imported_profiles,
            'companies': imported_companies,
            'skipped': skipped,
            'errors': errors
        }

    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to read CSV file: {str(e)}")


@import_cmd.command('all')
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--mode', type=click.Choice(['bulk', 'separate']), default='bulk',
              help='Import mode: bulk (all at once) or separate (confirm each)')
@click.option('--allow-duplicates', is_flag=True, help='Allow duplicate records')
@click.pass_context
def import_all(ctx, csv_file, mode, allow_duplicates):
    """Import all data from CSV file (exported with 'export all')

    The CSV file must have a 'Type' column to distinguish profiles from companies.

    Example:
        leadsauce import all data.csv
        leadsauce import all data.csv --mode separate
        leadsauce import all data.csv --allow-duplicates
    """
    try:
        csv_path = Path(csv_file).expanduser().resolve()

        click.echo(f"Importing data from: {csv_path}")
        click.echo(f"Mode: {mode}")
        click.echo()

        session = get_session()

        result = import_all_from_csv(
            session,
            csv_path,
            mode=mode,
            skip_duplicates=not allow_duplicates
        )

        click.echo()
        print_success(f"Import completed!")
        click.echo(f"  Profiles imported: {result['profiles']}")
        click.echo(f"  Companies imported: {result['companies']}")
        if result['skipped'] > 0:
            click.echo(f"  Skipped (duplicates): {result['skipped']}")

        if result['errors']:
            click.echo()
            click.secho(f"Errors ({len(result['errors'])}):", fg='yellow')
            for error in result['errors'][:10]:  # Show first 10 errors
                click.secho(f"  • {error}", fg='yellow')
            if len(result['errors']) > 10:
                click.secho(f"  ... and {len(result['errors']) - 10} more errors", fg='yellow')

    except Exception as e:
        print_error(f"Import failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@import_cmd.command('profiles')
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--mode', type=click.Choice(['bulk', 'separate']), default='bulk',
              help='Import mode: bulk (all at once) or separate (confirm each)')
@click.option('--allow-duplicates', is_flag=True, help='Allow duplicate emails')
@click.pass_context
def import_profiles(ctx, csv_file, mode, allow_duplicates):
    """Import profiles from CSV file

    CSV format must match the profiles export format with columns:
    ID, Name, Seniority, Email, Phone, Company, Generation, Married, Children, Skills, Tags, Notes

    Example:
        leadsauce import profiles contacts.csv
        leadsauce import profiles contacts.csv --mode separate
    """
    try:
        csv_path = Path(csv_file).expanduser().resolve()

        click.echo(f"Importing profiles from: {csv_path}")
        click.echo(f"Mode: {mode}")
        click.echo()

        session = get_session()

        imported, skipped, errors = import_profiles_from_csv(
            session,
            csv_path,
            mode=mode,
            skip_duplicates=not allow_duplicates
        )

        click.echo()
        print_success(f"Import completed!")
        click.echo(f"  Imported: {imported}")
        if skipped > 0:
            click.echo(f"  Skipped (duplicates): {skipped}")

        if errors:
            click.echo()
            click.secho(f"Errors ({len(errors)}):", fg='yellow')
            for error in errors[:10]:
                click.secho(f"  • {error}", fg='yellow')
            if len(errors) > 10:
                click.secho(f"  ... and {len(errors) - 10} more errors", fg='yellow')

    except Exception as e:
        print_error(f"Import failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@import_cmd.command('companies')
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--mode', type=click.Choice(['bulk', 'separate']), default='bulk',
              help='Import mode: bulk (all at once) or separate (confirm each)')
@click.option('--allow-duplicates', is_flag=True, help='Allow duplicate names')
@click.pass_context
def import_companies(ctx, csv_file, mode, allow_duplicates):
    """Import companies from CSV file

    CSV format must match the companies export format with columns:
    ID, Name, Industry, Size, Location, Website, Profiles, Notes

    Example:
        leadsauce import companies organizations.csv
        leadsauce import companies organizations.csv --mode separate
    """
    try:
        csv_path = Path(csv_file).expanduser().resolve()

        click.echo(f"Importing companies from: {csv_path}")
        click.echo(f"Mode: {mode}")
        click.echo()

        session = get_session()

        imported, skipped, errors = import_companies_from_csv(
            session,
            csv_path,
            mode=mode,
            skip_duplicates=not allow_duplicates
        )

        click.echo()
        print_success(f"Import completed!")
        click.echo(f"  Imported: {imported}")
        if skipped > 0:
            click.echo(f"  Skipped (duplicates): {skipped}")

        if errors:
            click.echo()
            click.secho(f"Errors ({len(errors)}):", fg='yellow')
            for error in errors[:10]:
                click.secho(f"  • {error}", fg='yellow')
            if len(errors) > 10:
                click.secho(f"  ... and {len(errors) - 10} more errors", fg='yellow')

    except Exception as e:
        print_error(f"Import failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()
