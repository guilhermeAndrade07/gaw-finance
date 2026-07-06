from celery import shared_task
from django.utils import timezone


@shared_task(bind=True)
def debug_task(self):
    timestamp = timezone.now().isoformat()
    return f'GAW Finance Celery is working. Task ID: {self.request.id}, Time: {timestamp}'
