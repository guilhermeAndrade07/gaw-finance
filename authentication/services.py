from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


def blacklist_user_tokens(user):
    tokens = OutstandingToken.objects.filter(
        user=user,
        expires_at__gt=timezone.now(),
    )

    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)
