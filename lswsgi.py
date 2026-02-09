"""
LiteSpeed WSGI entry point for LakeView College.
cPanel/LiteSpeed looks for 'lswsgi' - use this file and name it 'lswsgi' on the server,
or configure the app to use passenger_wsgi.py / lswsgi.py instead.
"""
import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

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
