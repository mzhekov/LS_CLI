#!/usr/bin/env python3
"""
Startup script for the LeadSauce AI Assistant API.

Usage:
    python run_api.py

Environment variables:
    ANTHROPIC_API_KEY     Required — your Anthropic API key
    LEADSAUCE_API_KEY     Recommended — shared secret for n8n → API auth
                          (leave empty to disable auth, dev mode only)
    FLASK_HOST            Host to bind (default: 0.0.0.0)
    FLASK_PORT            Port to listen on (default: 5055)
    FLASK_DEBUG           Set to '1' for debug mode (never in production)

n8n HTTP Request node setup:
    Method: POST
    URL:    http://<your-host>:5055/api/chat
    Header: X-API-Key: <LEADSAUCE_API_KEY>
    Body (JSON):
        {
          "message": "{{ $json.message }}",
          "session_id": "{{ $json.chat_id }}",
          "trigger_type": "morning_checkin",
          "external_context": "Meeting at 14:00 with the team"
        }
"""

import os
import sys

# Ensure the package is importable when run from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Validate required env vars before doing anything else
if not os.environ.get('ANTHROPIC_API_KEY'):
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
    print("       Export it before starting: export ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)

if not os.environ.get('LEADSAUCE_API_KEY'):
    print("WARNING: LEADSAUCE_API_KEY is not set — API auth is DISABLED (dev mode).")
    print("         Set it in production: export LEADSAUCE_API_KEY=<your-secret>")

from leadsauce.api.app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5055))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    print(f"LeadSauce AI Assistant API starting on http://{host}:{port}")
    print(f"  Debug mode : {debug}")
    print(f"  Auth key   : {'set' if os.environ.get('LEADSAUCE_API_KEY') else 'DISABLED'}")
    print()
    print("Available endpoints:")
    print("  POST /api/chat              — main chat")
    print("  GET  /api/context           — current context snapshot")
    print("  GET  /api/tasks             — active tasks")
    print("  GET  /api/goals             — active goals")
    print("  GET  /api/reminders         — upcoming reminders")
    print("  GET  /api/sessions          — conversation sessions")
    print("  GET  /api/sessions/<id>     — session history")
    print("  GET  /api/status            — health + quick stats")
    print("  GET  /health                — liveness check")
    print()

    app.run(host=host, port=port, debug=debug)
