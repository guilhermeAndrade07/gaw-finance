import hashlib
import time

from django.conf import settings
from django.core.cache import caches


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or 'unknown'


def _cache_key(scope, identifier, window_seconds):
    now = int(time.time())
    bucket = now // window_seconds
    identity = hashlib.sha256(f'{scope}:{identifier}:{bucket}'.encode()).hexdigest()
    return f'ratelimit:{identity}'


def is_rate_limited(scope, identifier):
    config = settings.AUTH_RATE_LIMITS[scope]
    limit = config['limit']
    window_seconds = config['window_seconds']
    key = _cache_key(scope, identifier, window_seconds)
    cache = caches['default']

    if cache.add(key, 1, timeout=window_seconds + 1):
        return False

    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window_seconds + 1)
        return False

    return count > limit


def is_login_rate_limited(request, email=''):
    client_ip = get_client_ip(request)
    if is_rate_limited('login', client_ip):
        return True

    normalized_email = email.strip().lower()
    if normalized_email and is_rate_limited('login', normalized_email):
        return True

    return False


def is_mfa_rate_limited(request, user):
    client_ip = get_client_ip(request)
    if is_rate_limited('mfa_verify', client_ip):
        return True

    if is_rate_limited('mfa_verify', user.pk):
        return True

    return False


def is_mfa_setup_rate_limited(request, user):
    client_ip = get_client_ip(request)
    if is_rate_limited('mfa_setup', client_ip):
        return True

    if is_rate_limited('mfa_setup', user.pk):
        return True

    return False


def is_invite_rate_limited(request):
    return is_rate_limited('invite_accept', get_client_ip(request))
