#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
# This file is used to execute various Django commands such as running the development server, applying database migrations, creating superusers, and custom management commands like building the chatbot index.
# Usage examples:
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_connect.settings')
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
