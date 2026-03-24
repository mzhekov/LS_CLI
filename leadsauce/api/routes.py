"""
REST API routes consumed by n8n workflows and the Telegram bot integration.

Authentication: set LEADSAUCE_API_KEY env var and pass it as X-API-Key header.
If LEADSAUCE_API_KEY is empty, auth is disabled (dev mode).

Endpoints:
  POST /api/chat            — main chat endpoint
  GET  /api/context         — current context snapshot
  GET  /api/tasks           — task summary
  GET  /api/goals           — goals summary
  GET  /api/reminders       — upcoming reminders
  GET  /api/sessions        — list conversation sessions
  GET  /api/sessions/<id>   — messages for a session
  GET  /api/status          — health + quick stats

  GET    /api/rules              — list all rules
  POST   /api/rules              — create a rule
  GET    /api/rules/<id>         — get a single rule
  PUT    /api/rules/<id>         — update a rule
  DELETE /api/rules/<id>         — delete a rule
  PATCH  /api/rules/<id>/toggle  — enable / disable a rule
"""

import logging
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

from leadsauce.services.ai_assistant import AIAssistantService
from leadsauce.services.context_builder import ContextBuilder
from leadsauce.utils.db import DatabaseSession
from leadsauce.models.task import Task
from leadsauce.models.goal import Goal
from leadsauce.models.reminder import Reminder
from leadsauce.models.rule import Rule, VALID_SCOPES

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

# Lazy singletons — created on first request
_assistant: AIAssistantService = None
_context_builder: ContextBuilder = None


def get_assistant() -> AIAssistantService:
    global _assistant
    if _assistant is None:
        _assistant = AIAssistantService()
    return _assistant


def get_context_builder() -> ContextBuilder:
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

def require_api_key(f):
    """Decorator that enforces X-API-Key header when LEADSAUCE_API_KEY is set."""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected_key = current_app.config.get('API_KEY', '')
        if expected_key:  # Only enforce if a key is configured
            provided = request.headers.get('X-API-Key', '')
            if provided != expected_key:
                return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------

@api_bp.route('/chat', methods=['POST'])
@require_api_key
def chat():
    """
    Main endpoint called by n8n for every Telegram message or scheduled trigger.

    Request body (JSON):
      message          str  — the user's text (required)
      session_id       str  — Telegram chat ID or any unique identifier (required)
      trigger_type     str  — one of: morning_checkin, evening_review, weekly_summary,
                              re_anchor, progress_report, setback_report, free_form
                              (default: free_form)
      external_context str  — optional extra context from n8n (calendar events, etc.)

    Response (JSON):
      response     str  — AI assistant reply
      session_id   str  — echoed back
      trigger_type str  — echoed back
    """
    data = request.get_json(silent=True) or {}

    message = (data.get('message') or '').strip()
    session_id = (data.get('session_id') or '').strip()
    trigger_type = data.get('trigger_type', 'free_form')
    external_context = data.get('external_context', '')

    if not message:
        return jsonify({'error': 'message is required'}), 400
    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    valid_triggers = {
        'morning_checkin', 'evening_review', 'weekly_summary',
        're_anchor', 'progress_report', 'setback_report', 'free_form',
    }
    if trigger_type not in valid_triggers:
        trigger_type = 'free_form'

    try:
        assistant = get_assistant()
        response_text = assistant.chat(
            message=message,
            session_id=session_id,
            trigger_type=trigger_type,
            external_context=external_context or None,
        )
        return jsonify({
            'response': response_text,
            'session_id': session_id,
            'trigger_type': trigger_type,
        })
    except EnvironmentError as e:
        logger.error("Config error: %s", e)
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        logger.exception("Error in /chat")
        return jsonify({'error': 'AI service error', 'detail': str(e)}), 500


# ---------------------------------------------------------------------------
# Context endpoint — n8n can call this to get a pre-built context block
# ---------------------------------------------------------------------------

@api_bp.route('/context', methods=['GET'])
@require_api_key
def context():
    """
    Returns the current context snapshot.

    Query params:
      external_context  str  — optional calendar / external info to include

    Response (JSON):
      context_block  str   — formatted [CONTEXT]...[/CONTEXT] string
      data           dict  — raw context data for n8n processing
    """
    external = request.args.get('external_context', '')
    builder = get_context_builder()
    try:
        raw = builder.get_raw_context()
        block = builder.build_context_block(external or None)
        return jsonify({'context_block': block, 'data': raw})
    except Exception as e:
        logger.exception("Error in /context")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Task summary
# ---------------------------------------------------------------------------

@api_bp.route('/tasks', methods=['GET'])
@require_api_key
def tasks():
    """
    Returns active tasks.

    Query params:
      status   str   — filter by status (default: pending,in_progress)
      limit    int   — max results (default: 20)
    """
    status_filter = request.args.get('status', 'pending,in_progress')
    statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
    limit = min(int(request.args.get('limit', 20)), 100)

    try:
        with DatabaseSession() as session:
            from datetime import datetime
            tasks_q = (
                session.query(Task)
                .filter(Task.status.in_(statuses))
                .order_by(Task.priority.desc(), Task.due_date.asc())
                .limit(limit)
                .all()
            )
            now = datetime.utcnow()
            result = []
            for t in tasks_q:
                d = t.to_dict()
                d['is_overdue'] = t.is_overdue()
                result.append(d)
        return jsonify({'tasks': result, 'count': len(result)})
    except Exception as e:
        logger.exception("Error in /tasks")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Goals summary
# ---------------------------------------------------------------------------

@api_bp.route('/goals', methods=['GET'])
@require_api_key
def goals():
    """
    Returns goals.

    Query params:
      status  str  — filter by status (default: active)
      limit   int  — max results (default: 10)
    """
    status_filter = request.args.get('status', 'active')
    statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
    limit = min(int(request.args.get('limit', 10)), 50)

    try:
        with DatabaseSession() as session:
            goals_q = (
                session.query(Goal)
                .filter(Goal.status.in_(statuses))
                .order_by(Goal.priority.desc(), Goal.progress.desc())
                .limit(limit)
                .all()
            )
            result = [g.to_dict(include_relations=False) for g in goals_q]
        return jsonify({'goals': result, 'count': len(result)})
    except Exception as e:
        logger.exception("Error in /goals")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

@api_bp.route('/reminders', methods=['GET'])
@require_api_key
def reminders():
    """
    Returns upcoming reminders.

    Query params:
      days    int  — how many days ahead (default: 7)
      limit   int  — max results (default: 10)
    """
    from datetime import datetime, timedelta
    days = min(int(request.args.get('days', 7)), 90)
    limit = min(int(request.args.get('limit', 10)), 50)

    try:
        with DatabaseSession() as session:
            now = datetime.utcnow()
            horizon = now + timedelta(days=days)
            reminders_q = (
                session.query(Reminder)
                .filter(
                    Reminder.completed == False,
                    Reminder.due_date != None,
                    Reminder.due_date >= now,
                    Reminder.due_date <= horizon,
                )
                .order_by(Reminder.due_date.asc())
                .limit(limit)
                .all()
            )
            result = [r.to_dict() for r in reminders_q]
        return jsonify({'reminders': result, 'count': len(result)})
    except Exception as e:
        logger.exception("Error in /reminders")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Conversation session history
# ---------------------------------------------------------------------------

@api_bp.route('/sessions', methods=['GET'])
@require_api_key
def sessions():
    """Returns all conversation sessions with last activity and message count."""
    try:
        assistant = get_assistant()
        return jsonify({'sessions': assistant.list_sessions()})
    except Exception as e:
        logger.exception("Error in /sessions")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/sessions/<session_id>', methods=['GET'])
@require_api_key
def session_history(session_id: str):
    """
    Returns conversation history for a specific session.

    Query params:
      limit   int  — max messages (default: 50)
    """
    limit = min(int(request.args.get('limit', 50)), 200)
    try:
        assistant = get_assistant()
        history = assistant.get_session_history(session_id, limit=limit)
        return jsonify({'session_id': session_id, 'messages': history, 'count': len(history)})
    except Exception as e:
        logger.exception("Error in /sessions/<id>")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Status / health with quick stats
# ---------------------------------------------------------------------------

@api_bp.route('/status', methods=['GET'])
@require_api_key
def status():
    """Returns service health and quick stats summary."""
    try:
        builder = get_context_builder()
        raw = builder.get_raw_context()
        return jsonify({
            'status': 'ok',
            'tasks': raw['task_counts'],
            'active_goals': len(raw['goals']),
            'upcoming_reminders': len(raw['upcoming_reminders']),
            'days_since_checkin': raw['days_since_checkin'],
        })
    except Exception as e:
        logger.exception("Error in /status")
        return jsonify({'status': 'degraded', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Rules — user-defined instructions that shape AI behavior
# ---------------------------------------------------------------------------

def _parse_rule_body(data: dict) -> tuple[dict, str | None]:
    """Validate and extract rule fields from request body. Returns (fields, error)."""
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    scope = (data.get('scope') or 'always').strip()
    priority = data.get('priority', 50)
    is_active = data.get('is_active', True)

    if not title:
        return {}, 'title is required'
    if not content:
        return {}, 'content is required'

    # Validate each scope token
    scope_tokens = [s.strip() for s in scope.split(',') if s.strip()]
    if not scope_tokens:
        return {}, 'scope cannot be empty'
    invalid = [s for s in scope_tokens if s not in VALID_SCOPES]
    if invalid:
        return {}, f"invalid scope value(s): {', '.join(invalid)}. Valid: {', '.join(sorted(VALID_SCOPES))}"

    try:
        priority = int(priority)
    except (TypeError, ValueError):
        return {}, 'priority must be an integer'

    return {
        'title': title,
        'content': content,
        'scope': ','.join(scope_tokens),
        'priority': max(0, min(priority, 1000)),
        'is_active': bool(is_active),
    }, None


@api_bp.route('/rules', methods=['GET'])
@require_api_key
def list_rules():
    """
    List all rules, optionally filtered.

    Query params:
      active_only  bool  — '1' or 'true' to return only active rules (default: false)
      scope        str   — filter by scope token (e.g. 'morning_checkin')
    """
    active_only = request.args.get('active_only', '').lower() in ('1', 'true')
    scope_filter = request.args.get('scope', '').strip()

    try:
        with DatabaseSession() as session:
            q = session.query(Rule)
            if active_only:
                q = q.filter(Rule.is_active == True)
            rules = q.order_by(Rule.priority.asc(), Rule.created_at.asc()).all()

            if scope_filter:
                rules = [r for r in rules if r.applies_to(scope_filter)]

            return jsonify({'rules': [r.to_dict() for r in rules], 'count': len(rules)})
    except Exception as e:
        logger.exception("Error in GET /rules")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/rules', methods=['POST'])
@require_api_key
def create_rule():
    """
    Create a new rule.

    Request body (JSON):
      title     str   — short label, e.g. "Language preference"         (required)
      content   str   — the instruction text injected into system prompt (required)
      scope     str   — 'always' or trigger type(s) comma-separated
                        valid values: always, morning_checkin, evening_review,
                        weekly_summary, re_anchor, progress_report,
                        setback_report, free_form
                        (default: 'always')
      priority  int   — sort order; lower = applied first (default: 50)
      is_active bool  — whether the rule is active (default: true)

    Response: the created rule object.
    """
    data = request.get_json(silent=True) or {}
    fields, error = _parse_rule_body(data)
    if error:
        return jsonify({'error': error}), 400

    try:
        with DatabaseSession() as session:
            rule = Rule(**fields)
            session.add(rule)
            session.flush()
            result = rule.to_dict()
        return jsonify(result), 201
    except Exception as e:
        logger.exception("Error in POST /rules")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/rules/<int:rule_id>', methods=['GET'])
@require_api_key
def get_rule(rule_id: int):
    """Get a single rule by ID."""
    try:
        with DatabaseSession() as session:
            rule = session.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return jsonify({'error': 'Rule not found'}), 404
            return jsonify(rule.to_dict())
    except Exception as e:
        logger.exception("Error in GET /rules/<id>")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@require_api_key
def update_rule(rule_id: int):
    """
    Replace a rule's fields.
    Accepts the same body as POST /api/rules.
    All fields are optional — only provided fields are updated.
    """
    data = request.get_json(silent=True) or {}

    try:
        with DatabaseSession() as session:
            rule = session.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return jsonify({'error': 'Rule not found'}), 404

            # Only update fields that were explicitly provided
            updatable = {}
            if 'title' in data:
                updatable['title'] = (data['title'] or '').strip()
                if not updatable['title']:
                    return jsonify({'error': 'title cannot be empty'}), 400

            if 'content' in data:
                updatable['content'] = (data['content'] or '').strip()
                if not updatable['content']:
                    return jsonify({'error': 'content cannot be empty'}), 400

            if 'scope' in data:
                scope_tokens = [s.strip() for s in str(data['scope']).split(',') if s.strip()]
                invalid = [s for s in scope_tokens if s not in VALID_SCOPES]
                if invalid:
                    return jsonify({'error': f"invalid scope: {', '.join(invalid)}"}), 400
                updatable['scope'] = ','.join(scope_tokens)

            if 'priority' in data:
                try:
                    updatable['priority'] = max(0, min(int(data['priority']), 1000))
                except (TypeError, ValueError):
                    return jsonify({'error': 'priority must be an integer'}), 400

            if 'is_active' in data:
                updatable['is_active'] = bool(data['is_active'])

            for key, value in updatable.items():
                setattr(rule, key, value)

            result = rule.to_dict()
        return jsonify(result)
    except Exception as e:
        logger.exception("Error in PUT /rules/<id>")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@require_api_key
def delete_rule(rule_id: int):
    """Delete a rule permanently."""
    try:
        with DatabaseSession() as session:
            rule = session.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return jsonify({'error': 'Rule not found'}), 404
            session.delete(rule)
        return jsonify({'deleted': rule_id})
    except Exception as e:
        logger.exception("Error in DELETE /rules/<id>")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/rules/<int:rule_id>/toggle', methods=['PATCH'])
@require_api_key
def toggle_rule(rule_id: int):
    """
    Enable or disable a rule without deleting it.

    Optional body: {"is_active": true/false}
    If omitted, flips the current state.
    """
    data = request.get_json(silent=True) or {}
    try:
        with DatabaseSession() as session:
            rule = session.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return jsonify({'error': 'Rule not found'}), 404

            if 'is_active' in data:
                rule.is_active = bool(data['is_active'])
            else:
                rule.is_active = not rule.is_active

            result = rule.to_dict()
        return jsonify(result)
    except Exception as e:
        logger.exception("Error in PATCH /rules/<id>/toggle")
        return jsonify({'error': str(e)}), 500
