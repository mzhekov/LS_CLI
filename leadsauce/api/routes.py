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
