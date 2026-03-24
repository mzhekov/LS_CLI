"""
WSGI entry point for production servers (gunicorn, uwsgi).
Gunicorn usage: gunicorn wsgi:app
"""
from leadsauce.api.app import create_app

app = create_app()
