from django.shortcuts import redirect

from .models import MFASetup


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

                if not request.session.get('mfa_verified') or request.session.get('mfa_verified_user_id') != user.pk:
                    return redirect('mfa_verify')

        return self.get_response(request)
