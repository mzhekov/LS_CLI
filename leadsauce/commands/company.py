"""
Company management commands
"""

import click
import json
from tabulate import tabulate
from leadsauce.utils.db import get_session
from leadsauce.utils.formatters import print_success, print_error, print_info, format_date
from leadsauce.models.company import Company
from leadsauce.models.profile import Profile


@click.group()
def company():
    """Company management commands"""
    pass


@company.command('create')
@click.option('--name', required=True, help='Company name')
@click.option('--industry', help='Industry')
@click.option('--size', help='Company size')
@click.option('--location', help='Location')
@click.option('--website', help='Website URL')
@click.option('--notes', help='Notes')

@click.pass_context
def create_company(ctx, name, industry, size, location, website, notes):
    """Create a new company"""

    try:
        session = get_session()

        # Check if company already exists
        existing = session.query(Company).filter(
            1==1,
            Company.name.ilike(name)
        ).first()

        if existing:
            print_error(f"Company '{name}' already exists (ID: {existing.id})")
            raise click.Abort()

        # Create company
        new_company = Company(
            
            name=name,
            industry=industry,
            size=size,
            location=location,
            website=website,
            notes=notes
        )

        session.add(new_company)
        session.commit()

        print_success(f"Company created successfully (ID: {new_company.id})")
        click.echo(f"Name: {new_company.name}")
        if industry:
            click.echo(f"Industry: {industry}")

    except Exception as e:
        print_error(f"Failed to create company: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@company.command('list')
@click.option('--limit', default=50, help='Number of results')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.option('--industry', help='Filter by industry')

@click.pass_context
def list_companies(ctx, limit, output_format, industry):
    """List companies"""

    try:
        session = get_session()

        query = session.query(Company).filter(1==1)

        if industry:
            query = query.filter(Company.industry.ilike(f"%{industry}%"))

        companies = query.limit(limit).all()

        if output_format == 'json':
            output = [c.to_dict(include_profiles=True) for c in companies]
            click.echo(json.dumps(output, indent=2, default=str))

        elif output_format == 'csv':
            import csv
            import sys
            writer = csv.writer(sys.stdout)
            writer.writerow(['ID', 'Name', 'Industry', 'Size', 'Location', 'Contacts'])
            for c in companies:
                writer.writerow([
                    c.id,
                    c.name,
                    c.industry or '',
                    c.size or '',
                    c.location or '',
                    len(c.profiles)
                ])

        else:  # table
            if companies:
                headers = ['ID', 'Name', 'Industry', 'Size', 'Location', 'Contacts']
                rows = []
                for c in companies:
                    rows.append([
                        c.id,
                        c.name[:30],
                        (c.industry or '-')[:20],
                        c.size or '-',
                        (c.location or '-')[:25],
                        len(c.profiles)
                    ])

                click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
                click.echo(f"\nShowing {len(companies)} companies")
            else:
                print_info("No companies found")

    except Exception as e:
        print_error(f"Failed to list companies: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@company.command('show')
@click.argument('company_id', type=int)
@click.option('--show-contacts', is_flag=True, help='Show associated contacts')

@click.pass_context
def show_company(ctx, company_id, show_contacts):
    """Show company details"""

    try:
        session = get_session()

        company = session.query(Company).filter(
            Company.id == company_id,
            1==1
        ).first()

        if not company:
            print_error(f"Company not found")
            raise click.Abort()

        click.echo()
        click.secho(f"{company.name}", fg='cyan', bold=True)
        click.echo('=' * 70)
        click.echo(f"ID:                {company.id}")
        click.echo(f"Industry:          {company.industry or 'N/A'}")
        click.echo(f"Size:              {company.size or 'N/A'}")
        click.echo(f"Location:          {company.location or 'N/A'}")
        click.echo(f"Website:           {company.website or 'N/A'}")
        click.echo(f"Contacts:          {len(company.profiles)}")
        click.echo(f"Created:           {format_date(company.created_at)}")

        if company.notes:
            click.echo(f"\nNotes:")
            click.echo(f"{company.notes}")

        if show_contacts and company.profiles:
            click.echo(f"\nContacts:")
            for p in company.profiles[:10]:
                click.echo(f"  • {p.name} ({p.seniority})")
            if len(company.profiles) > 10:
                click.echo(f"  ... and {len(company.profiles) - 10} more")

        click.echo()

    except Exception as e:
        print_error(f"Failed to show company: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@company.command('delete')
@click.argument('company_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation')

@click.pass_context
def delete_company(ctx, company_id, force):
    """Delete a company"""

    try:
        session = get_session()

        company = session.query(Company).filter(
            Company.id == company_id,
            1==1
        ).first()

        if not company:
            print_error(f"Company not found")
            raise click.Abort()

        contact_count = len(company.profiles)

        # Confirmation
        if not force:
            msg = f"Delete company '{company.name}'?"
            if contact_count > 0:
                msg += f" ({contact_count} contacts will be unlinked)"

            if not click.confirm(msg):
                click.echo("Operation cancelled")
                raise click.Abort()

        name = company.name
        session.delete(company)
        session.commit()

        print_success(f"Company '{name}' deleted successfully")

    except Exception as e:
        print_error(f"Failed to delete company: {str(e)}")
        raise click.Abort()
    finally:
        session.close()
