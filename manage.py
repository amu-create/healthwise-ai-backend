#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthwise.settings')
    
    # Railway 환경에서 DATABASE_URL 디버깅
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("🚂 Running in Railway environment")
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
        else:
            print("⚠️ DATABASE_URL is not set yet")
            print("📋 Available environment variables:")
            for key in sorted(os.environ.keys()):
                if 'DATABASE' in key or 'POSTGRES' in key:
                    print(f"  {key}: {os.environ[key][:50] if os.environ[key] else 'EMPTY'}...")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
