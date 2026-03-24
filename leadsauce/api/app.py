"""
Flask application factory for the AI assistant REST API.
Called by n8n workflows to get context and chat with Miro's personal coach.
"""

import os
import logging
from flask import Flask
from leadsauce.utils.db import init_database


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Secret key for session (not used for auth — we use API key headers)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'leadsauce-ai-dev-key')

    # API key for protecting the endpoints (n8n sets this header)
    app.config['API_KEY'] = os.environ.get('LEADSAUCE_API_KEY', '')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    # Initialize the database (creates tables if missing)
    init_database()

    # Register routes blueprint
    from leadsauce.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'leadsauce-ai-assistant'}

    return app
