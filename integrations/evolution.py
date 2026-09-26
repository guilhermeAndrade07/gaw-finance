import logging

import requests

from django.conf import settings

logger = logging.getLogger(__name__)


class EvolutionAPIError(Exception):
    pass


def _headers():
    return {'apikey': settings.EVOLUTION_API_KEY, 'Content-Type': 'application/json'}


def _base_url():
    return settings.EVOLUTION_API_URL.rstrip('/')


def _handle_response(response, action):
    if response.status_code in (200, 201):
        return response.json() if response.content else {}
    logger.error('Evolution API falhou em %s: %s %s', action, response.status_code, response.text[:300])
    raise EvolutionAPIError(f'Evolution API falhou em {action} (status {response.status_code}).')


def get_instance_status(instance=None):
    instance = instance or settings.EVOLUTION_INSTANCE_NAME
    response = requests.get(
        f'{_base_url()}/instance/connectionState/{instance}',
        headers=_headers(),
        timeout=10,
    )
    return _handle_response(response, 'connectionState')


def create_instance(instance=None):
    instance = instance or settings.EVOLUTION_INSTANCE_NAME
    response = requests.post(
        f'{_base_url()}/instance/create',
        headers=_headers(),
        json={
            'instanceName': instance,
            'qrcode': True,
            'integration': 'WHATSAPP-BAILEYS',
        },
        timeout=30,
    )
    return _handle_response(response, 'createInstance')


def get_qr_code(instance=None):
    instance = instance or settings.EVOLUTION_INSTANCE_NAME
    response = requests.get(
        f'{_base_url()}/instance/connect/{instance}',
        headers=_headers(),
        timeout=15,
    )
    return _handle_response(response, 'connect')


def send_text(number, text, instance=None):
    instance = instance or settings.EVOLUTION_INSTANCE_NAME
    response = requests.post(
        f'{_base_url()}/message/sendText/{instance}',
        headers=_headers(),
        json={
            'number': number,
            'text': text,
        },
        timeout=20,
    )
    return _handle_response(response, 'sendText')
