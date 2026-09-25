import logging

from .context import request_id_var
from .models import AuditEvent

logger = logging.getLogger(__name__)


def client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR') or None


def user_agent(request):
    return (request.META.get('HTTP_USER_AGENT') or '')[:255]


def record_audit_event(
    *,
    action,
    user=None,
    resource_type='',
    resource_id='',
    description='',
    status=AuditEvent.SUCCESS,
    metadata=None,
    request=None,
):
    event_user = user if user is not None and getattr(user, 'is_authenticated', False) else None
    event_username = event_user.get_username() if event_user else ''

    payload = {
        'action': action,
        'actor': event_user,
        'actor_username': event_username,
        'resource_type': str(resource_type or '')[:100],
        'resource_id': str(resource_id or '')[:100],
        'description': description or '',
        'status': status,
        'metadata': metadata or {},
    }

    if request is not None:
        payload['ip_address'] = client_ip(request)
        payload['user_agent'] = user_agent(request)

    try:
        event = AuditEvent.objects.create(
            request_id=request_id_var.get(''),
            **payload,
        )
        logger.info('Audit event recorded', extra={'context': {
            'audit_id': event.pk,
            'action': event.action,
            'resource_type': event.resource_type,
            'resource_id': event.resource_id,
            'status': event.status,
        }})
        return event
    except Exception:
        logger.exception('Failed to record audit event', extra={'context': {
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
        }})
        return None


def audit_success(action, **kwargs):
    return record_audit_event(action=action, status=AuditEvent.SUCCESS, **kwargs)


def audit_failure(action, **kwargs):
    return record_audit_event(action=action, status=AuditEvent.FAILURE, **kwargs)
