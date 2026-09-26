import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from integrations.models import WhatsAppBinding, WhatsAppMessageLog

logger = logging.getLogger(__name__)


def _unwrap_container(message):
    nested_types = (
        'ephemeralMessage',
        'viewOnceMessage',
        'viewOnceMessageV2',
        'documentWithCaptionMessage',
    )
    for _ in range(3):
        if not isinstance(message, dict):
            break
        for container in nested_types:
            inner = message.get(container)
            if isinstance(inner, dict) and isinstance(inner.get('message'), dict):
                message = inner['message']
                break
        else:
            break
    return message


def _extract_text(message):
    text = message.get('conversation')
    if not text:
        extended = message.get('extendedTextMessage') or {}
        text = extended.get('text')
    if not text:
        image = message.get('imageMessage') or {}
        text = image.get('caption')
    if not text:
        document = message.get('documentWithCaptionMessage') or {}
        inner = document.get('message') or {}
        text = inner.get('caption')
    return text


def _extract_message(payload):
    event = str(payload.get('event') or '').replace('.', '_').upper()
    if event != 'MESSAGES_UPSERT':
        logger.info('WhatsApp: evento ignorado event=%s body=%s', payload.get('event'), json.dumps(payload)[:400])
        return None

    data = payload.get('data') or {}
    key = data.get('key') or {}

    message = _unwrap_container(data.get('message') or {})
    text = _extract_text(message)

    if not text:
        logger.info('WhatsApp: mensagem sem texto extratavel. body=%s', json.dumps(payload)[:600])
        return None

    message_id = key.get('id')
    phone = (key.get('remoteJid') or '').split('@')[0]
    if not message_id or not phone:
        return None

    return {
        'message_id': message_id,
        'phone': phone,
        'text': text,
        'from_me': bool(key.get('fromMe')),
        'raw': payload,
    }


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    secret = request.headers.get('X-Webhook-Secret', '') or request.GET.get('secret', '')
    if secret != settings.WHATSAPP_WEBHOOK_SECRET:
        return JsonResponse({'detail': 'forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'detail': 'invalid payload'}, status=400)

    message = _extract_message(payload)
    if message is None:
        return JsonResponse({'detail': 'ignored'}, status=200)

    log, created = WhatsAppMessageLog.objects.get_or_create(
        message_id=message['message_id'],
        defaults={
            'direction': WhatsAppMessageLog.DIRECTION_IN,
            'phone': message['phone'],
            'raw_body': message['raw'],
            'message_text': message['text'],
        },
    )
    if not created:
        return JsonResponse({'detail': 'duplicate ignored'}, status=200)

    binding = WhatsAppBinding.objects.filter(
        phone__endswith=message['phone'],
        is_active=True,
    ).select_related('user').first()

    if binding is None:
        logger.info('WhatsApp: numero nao vinculado %s', message['phone'])
        log.result_status = WhatsAppMessageLog.STATUS_IGNORED
        log.save(update_fields=['result_status', 'update_at'])
        return JsonResponse({'detail': 'unbound number'}, status=200)

    log.binding = binding
    log.save(update_fields=['binding', 'update_at'])

    from integrations.tasks import process_whatsapp_message
    process_whatsapp_message.delay(message['message_id'])

    return JsonResponse({'detail': 'accepted'}, status=200)
