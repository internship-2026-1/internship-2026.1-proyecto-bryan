import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("core")

# Lee configuración desde settings.py (prefijo CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodescubre tareas en apps instaladas (tasks.py)
app.autodiscover_tasks()
