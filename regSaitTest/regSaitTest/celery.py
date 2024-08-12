from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Устанавливаем переменную окружения для Django настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'regSaitTest.settings')

app = Celery('regSaitTest')

# Загружаем настройки из файла settings.py с префиксом CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в файлах tasks.py всех приложений
app.autodiscover_tasks()

