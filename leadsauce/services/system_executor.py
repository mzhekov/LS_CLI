"""System Command Executor for AI Integration

This module executes LeadSauce system operations based on AI-generated commands,
enabling AI to perform actual operations (create reminders, profiles, etc.) rather
than just providing advice.
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dateutil import parser as date_parser

from leadsauce.utils.db import get_session
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.interaction import Interaction
from leadsauce.models.reminder import Reminder
from leadsauce.models.tag import Tag
from leadsauce.models.relationship import ProfileRelationship, CompanyRelationship


class SystemExecutor:
    """Executes LeadSauce system commands from AI"""

    @staticmethod
    def parse_natural_date(date_str: str) -> datetime:
        """Parse natural language dates into datetime objects

        Args:
            date_str: Natural language date (tomorrow, next week, Friday, etc.)

        Returns:
            datetime object
        """
        date_str = date_str.lower().strip()
        now = datetime.now()

        # Relative dates
        if date_str in ['today', 'now']:
            return now
        elif date_str == 'tomorrow':
            return now + timedelta(days=1)
        elif date_str == 'yesterday':
            return now - timedelta(days=1)
        elif 'next week' in date_str:
            return now + timedelta(days=7)
        elif 'next month' in date_str:
            return now + timedelta(days=30)

        # "in X days/weeks/months"
        match = re.match(r'in (\d+) (day|days|week|weeks|month|months)', date_str)
        if match:
            count = int(match.group(1))
            unit = match.group(2)
            if 'day' in unit:
                return now + timedelta(days=count)
            elif 'week' in unit:
                return now + timedelta(weeks=count)
            elif 'month' in unit:
                return now + timedelta(days=count * 30)

        # Try parsing as standard date format
        try:
            return date_parser.parse(date_str)
        except:
            # Default to tomorrow if can't parse
            return now + timedelta(days=1)

    @staticmethod
    def extract_commands(text: str) -> List[Dict[str, Any]]:
        """Extract JSON commands from AI response text

        Args:
            text: AI response text that may contain JSON commands

        Returns:
            List of command dictionaries
        """
        commands = []

        # Find all JSON code blocks
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                cmd = json.loads(match)
                if 'action' in cmd:
                    commands.append(cmd)
            except json.JSONDecodeError:
                continue

        return commands

    @staticmethod
    def execute_command(command: Dict[str, Any]) -> Tuple[bool, str, Any]:
        """Execute a single LeadSauce command

        Args:
            command: Command dictionary with 'action' and 'params'

        Returns:
            Tuple of (success, message, result_data)
        """
        action = command.get('action')
        params = command.get('params', {})

        session = get_session()
        try:
            if action == 'CREATE_REMINDER':
                return SystemExecutor._create_reminder(session, params)

            elif action == 'CREATE_PROFILE':
                return SystemExecutor._create_profile(session, params)

            elif action == 'CREATE_COMPANY':
                return SystemExecutor._create_company(session, params)

            elif action == 'CREATE_INTERACTION':
                return SystemExecutor._create_interaction(session, params)

            elif action == 'CREATE_TAG':
                return SystemExecutor._create_tag(session, params)

            elif action == 'CREATE_RELATIONSHIP':
                return SystemExecutor._create_relationship(session, params)

            elif action == 'SEARCH_PROFILES':
                return SystemExecutor._search_profiles(session, params)

            elif action == 'GET_STATS':
                return SystemExecutor._get_stats(session, params)

            elif action == 'LIST_REMINDERS':
                return SystemExecutor._list_reminders(session, params)

            else:
                return False, f"Unknown action: {action}", None

        except Exception as e:
            return False, f"Error executing {action}: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def _create_reminder(session, params: Dict) -> Tuple[bool, str, Any]:
        """Create a reminder"""
        title = params.get('title')
        if not title:
            return False, "Title is required for reminders", None

        due_date_str = params.get('due_date')
        if not due_date_str:
            return False, "Due date is required for reminders", None

        due_date = SystemExecutor.parse_natural_date(due_date_str)

        reminder = Reminder(
            title=title,
            description=params.get('description', ''),
            due_date=due_date,
            priority=params.get('priority', 'medium'),
            category=params.get('category', 'general'),
            profile_id=params.get('profile_id'),
            completed=False
        )

        session.add(reminder)
        session.commit()

        result = {
            'id': reminder.id,
            'title': reminder.title,
            'due_date': reminder.due_date.strftime('%Y-%m-%d %H:%M'),
            'priority': reminder.priority,
            'category': reminder.category
        }

        return True, f"✓ Created reminder #{reminder.id}: {title} (due {reminder.due_date.strftime('%Y-%m-%d')})", result

    @staticmethod
    def _create_profile(session, params: Dict) -> Tuple[bool, str, Any]:
        """Create a profile"""
        name = params.get('name')
        if not name:
            return False, "Name is required for profiles", None

        # Handle company
        company_id = None
        company_name = params.get('company_name')
        if company_name:
            company = session.query(Company).filter(
                Company.name == company_name
            ).first()
            if not company:
                # Create company if it doesn't exist
                company = Company(name=company_name)
                session.add(company)
                session.flush()
            company_id = company.id

        profile = Profile(
            name=name,
            email=params.get('email'),
            phone=params.get('phone'),
            company_id=company_id,
            title=params.get('title'),
            seniority=params.get('seniority'),
            generation=params.get('generation'),
            linkedin=params.get('linkedin')
        )

        session.add(profile)
        session.flush()

        # Handle tags
        tags_str = params.get('tags', '')
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(',')]
            for tag_name in tag_names:
                tag = session.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                profile.tags.append(tag)

        session.commit()

        result = {
            'id': profile.id,
            'name': profile.name,
            'email': profile.email,
            'company': company_name if company_name else None,
            'title': profile.title
        }

        return True, f"✓ Created profile #{profile.id}: {name}" + (f" at {company_name}" if company_name else ""), result

    @staticmethod
    def _create_company(session, params: Dict) -> Tuple[bool, str, Any]:
        """Create a company"""
        name = params.get('name')
        if not name:
            return False, "Name is required for companies", None

        # Check if company already exists
        existing = session.query(Company).filter(Company.name == name).first()
        if existing:
            return False, f"Company '{name}' already exists (ID: {existing.id})", None

        company = Company(
            name=name,
            industry=params.get('industry'),
            size=params.get('size'),
            website=params.get('website'),
            description=params.get('description')
        )

        session.add(company)
        session.commit()

        result = {
            'id': company.id,
            'name': company.name,
            'industry': company.industry,
            'size': company.size
        }

        return True, f"✓ Created company #{company.id}: {name}", result

    @staticmethod
    def _create_interaction(session, params: Dict) -> Tuple[bool, str, Any]:
        """Create an interaction"""
        profile_id = params.get('profile_id')
        if not profile_id:
            return False, "profile_id is required for interactions", None

        interaction_type = params.get('type')
        if not interaction_type:
            return False, "type is required for interactions", None

        notes = params.get('notes')
        if not notes:
            return False, "notes is required for interactions", None

        # Parse date
        date_str = params.get('date', 'today')
        interaction_date = SystemExecutor.parse_natural_date(date_str)

        # Verify profile exists
        profile = session.query(Profile).get(profile_id)
        if not profile:
            return False, f"Profile #{profile_id} not found", None

        interaction = Interaction(
            profile_id=profile_id,
            type=interaction_type,
            notes=notes,
            interaction_date=interaction_date
        )

        session.add(interaction)
        session.commit()

        result = {
            'id': interaction.id,
            'profile': profile.name,
            'type': interaction_type,
            'date': interaction_date.strftime('%Y-%m-%d')
        }

        return True, f"✓ Logged {interaction_type} with {profile.name}", result

    @staticmethod
    def _create_tag(session, params: Dict) -> Tuple[bool, str, Any]:
        """Create a tag"""
        name = params.get('name')
        if not name:
            return False, "Name is required for tags", None

        # Check if tag already exists
        existing = session.query(Tag).filter(Tag.name == name).first()
        if existing:
            return False, f"Tag '{name}' already exists (ID: {existing.id})", None

        tag = Tag(
            name=name,
            description=params.get('description')
        )

        session.add(tag)
        session.commit()

        result = {
            'id': tag.id,
            'name': tag.name
        }

        return True, f"✓ Created tag #{tag.id}: {name}", result

    @staticmethod
    def _create_relationship(session, params: Dict) -> Tuple[bool, str, Any]:
        """Create a relationship between profiles"""
        source_id = params.get('source_profile_id')
        target_id = params.get('target_profile_id')
        rel_type = params.get('relationship_type')

        if not all([source_id, target_id, rel_type]):
            return False, "source_profile_id, target_profile_id, and relationship_type are required", None

        # Verify profiles exist
        source = session.query(Profile).get(source_id)
        target = session.query(Profile).get(target_id)

        if not source:
            return False, f"Source profile #{source_id} not found", None
        if not target:
            return False, f"Target profile #{target_id} not found", None

        relationship = ProfileRelationship(
            from_profile_id=source_id,
            to_profile_id=target_id,
            relationship_type=rel_type
        )

        session.add(relationship)
        session.commit()

        result = {
            'id': relationship.id,
            'source': source.name,
            'target': target.name,
            'type': rel_type
        }

        return True, f"✓ Created relationship: {source.name} → {rel_type} → {target.name}", result

    @staticmethod
    def _search_profiles(session, params: Dict) -> Tuple[bool, str, Any]:
        """Search profiles"""
        query = session.query(Profile)

        # Apply filters
        if params.get('query'):
            search = f"%{params['query']}%"
            query = query.filter(
                (Profile.name.like(search)) |
                (Profile.email.like(search))
            )

        if params.get('company'):
            query = query.join(Company).filter(
                Company.name.like(f"%{params['company']}%")
            )

        if params.get('seniority'):
            query = query.filter(Profile.seniority == params['seniority'])

        if params.get('tag'):
            query = query.join(Profile.tags).filter(
                Tag.name == params['tag']
            )

        profiles = query.limit(20).all()

        result = [{
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'company': p.company.name if p.company else None,
            'title': p.title
        } for p in profiles]

        return True, f"Found {len(profiles)} profile(s)", result

    @staticmethod
    def _get_stats(session, params: Dict) -> Tuple[bool, str, Any]:
        """Get system statistics"""
        stats = {
            'profiles': session.query(Profile).count(),
            'companies': session.query(Company).count(),
            'active_reminders': session.query(Reminder).filter(
                Reminder.completed == False
            ).count(),
            'total_reminders': session.query(Reminder).count(),
            'interactions': session.query(Interaction).count(),
            'tags': session.query(Tag).count(),
            'relationships': session.query(ProfileRelationship).count() + session.query(CompanyRelationship).count()
        }

        return True, "System statistics", stats

    @staticmethod
    def _list_reminders(session, params: Dict) -> Tuple[bool, str, Any]:
        """List reminders"""
        query = session.query(Reminder).filter(Reminder.completed == False)

        # Sort by due date
        query = query.order_by(Reminder.due_date)

        # Limit
        limit = params.get('limit', 10)
        reminders = query.limit(limit).all()

        result = [{
            'id': r.id,
            'title': r.title,
            'due_date': r.due_date.strftime('%Y-%m-%d %H:%M'),
            'priority': r.priority,
            'category': r.category,
            'profile': r.profile.name if r.profile else None
        } for r in reminders]

        return True, f"Found {len(reminders)} active reminder(s)", result
