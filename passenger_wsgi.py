"""
cPanel / Passenger WSGI entry point for LakeView College.
Place this file in the same directory as manage.py (application root).
Adjust INTERP if your cPanel virtualenv path is different.
"""
import sys
import os

# Path to cPanel-created virtualenv (common: app_root/virtualenv)
# If your app root is e.g. public_html/lakeview, use: os.path.join(os.environ['HOME'], 'public_html', 'lakeview', 'virtualenv')
APP_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(APP_DIR, 'virtualenv', 'bin', 'python3')
if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)

sys.path.insert(0, APP_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lakeView_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
