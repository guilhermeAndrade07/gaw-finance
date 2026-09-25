from django.contrib.auth.models import User
from django.core.cache import caches
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.services import blacklist_user_tokens


class JWTFlowTests(TestCase):
    def setUp(self):
        caches['default'].clear()
        self.user = User.objects.create_user(
            username='jwt-user',
            email='jwt-user@gawfinance.com',
            password='senha-forte-123',
        )
        self.client = APIClient()

    def _authenticate(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'jwt-user', 'password': 'senha-forte-123'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        return response.data['refresh']

    def test_logout_revokes_refresh_token(self):
        refresh_token = self._authenticate()

        response = self.client.post(
            reverse('token_logout'),
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(response.status_code, 200)

        refresh_response = self.client.post(
            reverse('token_refresh'),
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_logout_rejects_invalid_refresh_token(self):
        response = self.client.post(
            reverse('token_logout'),
            {'refresh': 'invalid-token'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_blacklists_active_tokens(self):
        RefreshToken.for_user(self.user)
        RefreshToken.for_user(self.user)

        self.assertEqual(BlacklistedToken.objects.count(), 0)
        blacklist_user_tokens(self.user)
        self.assertEqual(BlacklistedToken.objects.count(), 2)


class JWTThrottleTests(TestCase):
    def setUp(self):
        caches['default'].clear()
        self.user = User.objects.create_user(
            username='jwt-throttle-user',
            email='jwt-throttle-user@gawfinance.com',
            password='senha-forte-123',
        )
        self.client = APIClient()

    @override_settings(
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ),
            'DEFAULT_PERMISSION_CLASSES': (
                'rest_framework.permissions.IsAuthenticated',
            ),
            'DEFAULT_THROTTLE_RATES': {
                'jwt_token': '10/min',
                'jwt_refresh': '30/min',
                'jwt_verify': '60/min',
                'jwt_logout': '10/min',
            },
        }
    )
    def test_token_obtain_is_rate_limited(self):
        for _ in range(11):
            response = self.client.post(
                reverse('token_obtain_pair'),
                {'username': 'jwt-throttle-user', 'password': 'senha-forte-123'},
                format='json',
            )

        self.assertEqual(response.status_code, 429)
