"""
WSGI config for regSaitTest project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import sys
import traceback
import time
import signal
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'regSaitTest.settings')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    application = get_wsgi_application()

except Exception:
    traceback.print_exc()
    if 'mod_wsgi' in sys.modules:
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)
