from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Устанавливаем переменную окружения для Django настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'regSaitTest.settings')
# os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# import django
# django.setup()
#
from django.conf import settings

app = Celery('regSaitTest')


# Загружаем настройки из файла settings.py с префиксом CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в файлах tasks.py всех приложений
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
