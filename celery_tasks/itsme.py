from celery import shared_task
from celery_tasks.tasks import send_active_mail, generate_index


@shared_task
def send_mail(recipient_list, user_name, token):
    send_active_mail(recipient_list, user_name, token)


@shared_task
def static_index():
    generate_index()


