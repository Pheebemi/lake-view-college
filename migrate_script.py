#!/usr/bin/env python
"""
Manual migration script to handle the database migration issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lakeView_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    try:
        # Run the migration
        execute_from_command_line(['manage.py', 'migrate', 'accounts'])
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()