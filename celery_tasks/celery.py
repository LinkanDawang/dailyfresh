import os
from celery import Celery
from django.apps import apps, AppConfig
from django.conf import settings


if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')

app = Celery('celery.tasks.celery', broker='amqp://leslie:admin@192.168.3.168:5672/administrator', backend='redis://192.168.3.168:6379/4')



class CeleryConfig(AppConfig):
    name = 'celery_tasks'
    verbose_name = 'Celery Config'

    def ready(self):
        app.config_from_object('django.conf:settings', force=True)
        install_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: install_apps, force=True)

