import logging
import uuid

from celery import shared_task

from django.utils import timezone

from integrations import evolution
from integrations.models import WhatsAppBinding, WhatsAppMessageLog
from integrations.handlers import process_message

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_whatsapp_message(self, message_id):
    log = WhatsAppMessageLog.objects.filter(message_id=message_id).select_related('binding__user').first()
    if log is None or log.direction != WhatsAppMessageLog.DIRECTION_IN:
        return

    if log.result_status not in (WhatsAppMessageLog.STATUS_PENDING,):
        return

    binding = log.binding
    if binding is None or not binding.is_active:
        log.result_status = WhatsAppMessageLog.STATUS_IGNORED
        log.save(update_fields=['result_status', 'update_at'])
        return

    try:
        response_text, interpretation = process_message(binding.user, log.message_text)
    except Exception as error:
        log.result_status = WhatsAppMessageLog.STATUS_ERROR
        log.response_text = str(error)[:2000]
        log.save(update_fields=['result_status', 'response_text', 'update_at'])
        raise self.retry(exc=error)

    if interpretation:
        log.interpreted_intent = interpretation.get('intent')
    log.response_text = response_text
    log.result_status = WhatsAppMessageLog.STATUS_PROCESSED
    log.save(update_fields=['interpreted_intent', 'response_text', 'result_status', 'update_at'])

    send_whatsapp_reply.delay(log.phone, response_text)


def _extract_sent_message_id(response):
    if not isinstance(response, dict):
        return None
    for container in ('messageData', 'message', None):
        source = response.get(container) if container else response
        if isinstance(source, dict):
            key = source.get('key') or {}
            if key.get('id'):
                return key['id']
    return None


@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def send_whatsapp_reply(self, phone, text):
    try:
        response = evolution.send_text(phone, text)
    except evolution.EvolutionAPIError as error:
        logger.error('Falha ao enviar resposta para %s: %s', phone, error)
        raise self.retry(exc=error)

    sent_id = _extract_sent_message_id(response) or f'SENT-{uuid.uuid4().hex}'
    binding = WhatsAppBinding.objects.filter(
        phone__endswith=phone,
        is_active=True,
    ).select_related('user').first()
    WhatsAppMessageLog.objects.get_or_create(
        message_id=sent_id,
        defaults={
            'binding': binding,
            'direction': WhatsAppMessageLog.DIRECTION_OUT,
            'phone': phone,
            'message_text': text,
            'result_status': WhatsAppMessageLog.STATUS_PROCESSED,
            'response_text': text,
        },
    )


@shared_task
def cleanup_old_whatsapp_logs(days=30):
    cutoff = timezone.now() - timezone.timedelta(days=days)
    WhatsAppMessageLog.objects.filter(created_at__lt=cutoff).delete()
