from datetime import timedelta

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone

from .models import MFASetup

MFA_VALIDITY = timedelta(
    hours=getattr(settings, 'MFA_VERIFICATION_VALIDITY_HOURS', 24),
)


def mfa_verification_is_valid(session, user_pk):
    """Retorna True quando a marca de MFA da sessão é do usuário e está dentro da janela de validade."""
    if not session.get('mfa_verified') or session.get('mfa_verified_user_id') != user_pk:
        return False

    verified_at = session.get('mfa_verified_at')
    if verified_at is None:
        # Marca criada antes do timestamp: continua válida nesta sessão.
        return True
    return timezone.now().timestamp() - verified_at <= MFA_VALIDITY.total_seconds()


class MFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and (user.is_staff or user.is_superuser):
            path = request.path
            allowed_prefixes = ('/mfa/', '/logout/', '/static/', '/media/')

            if not path.startswith(allowed_prefixes):
                setup = MFASetup.objects.filter(
                    user=user,
                    confirmed_at__isnull=False,
                ).first()

                if setup is None:
                    return redirect('mfa_setup')

                if not mfa_verification_is_valid(request.session, user.pk):
                    return redirect('mfa_verify')

        return self.get_response(request)
