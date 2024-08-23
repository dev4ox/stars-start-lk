#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import time
import traceback
import signal


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'regSaitTest.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    try:
        execute_from_command_line(sys.argv)

    except RuntimeError:
        traceback.print_exc()
        if 'mod_wsgi' in sys.modules:
            os.kill(os.getpid(), signal.SIGINT)
            time.sleep(2.5)


if __name__ == '__main__':
    main()
