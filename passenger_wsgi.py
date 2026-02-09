"""
cPanel / Passenger WSGI entry point for LakeView College.
Place this file in the same directory as manage.py (application root).
"""
import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# cPanel often creates venv at ~/virtualenv/<app_name>/<version>/bin/python3 (change 3.11 if you use another version)
HOME = os.environ.get('HOME', '')
VENV_PYTHON = os.path.join(HOME, 'virtualenv', 'lakeview', '3.11', 'bin', 'python3')
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.join(APP_DIR, 'virtualenv', 'bin', 'python3')
if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)

sys.path.insert(0, APP_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lakeView_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
