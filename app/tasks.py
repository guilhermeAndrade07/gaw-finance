from celery import shared_task
from django.utils import timezone


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_signature_charges():
    from signatures.services import generate_signature_charges as generate

    generate()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    acks_late=True,
    reject_on_worker_lost=True,
)
def close_past_invoices():
    from payment.services import close_past_invoices as close

    close()


@shared_task(bind=True)
def debug_task(self):
    timestamp = timezone.now().isoformat()
    return f'GAW Finance Celery is working. Task ID: {self.request.id}, Time: {timestamp}'
