import io
import re
from datetime import timedelta

import pyotp
from django.contrib.auth.models import User
from django.core.cache import caches
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from accounts.models import Account, Invite, MFASetup, RecoveryCode
from banks.models import Bank
from categories.defaults import DEFAULT_CATEGORY_NAMES
from categories.models import Category


class RateLimitTests(TestCase):
    def setUp(self):
        caches['default'].clear()

    @override_settings(
        AUTH_RATE_LIMITS={
            'login': {'limit': 2, 'window_seconds': 60},
            'mfa_setup': {'limit': 2, 'window_seconds': 60},
            'mfa_verify': {'limit': 2, 'window_seconds': 60},
            'invite_accept': {'limit': 2, 'window_seconds': 60},
        }
    )
    def test_login_is_rate_limited(self):
        User.objects.create_user(
            username='rate-login',
            email='rate-login@gawfinance.com',
            password='senha-forte-123',
        )

        for _ in range(3):
            response = self.client.post(reverse('login'), {
                'email': 'rate-login@gawfinance.com',
                'password': 'senha-errada',
            })

        self.assertEqual(response.status_code, 429)

    @override_settings(
        AUTH_RATE_LIMITS={
            'login': {'limit': 10, 'window_seconds': 300},
            'mfa_setup': {'limit': 2, 'window_seconds': 60},
            'mfa_verify': {'limit': 2, 'window_seconds': 60},
            'invite_accept': {'limit': 10, 'window_seconds': 3600},
        }
    )
    def test_mfa_verify_is_rate_limited(self):
        user = User.objects.create_user(
            username='rate-mfa',
            email='rate-mfa@gawfinance.com',
            password='senha-forte-123',
            is_staff=True,
            is_superuser=True,
        )
        MFASetup.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            confirmed_at=timezone.now(),
        )
        self.client.force_login(user)

        for _ in range(3):
            response = self.client.post(reverse('mfa_verify'), {'code': '000000'})

        self.assertEqual(response.status_code, 429)


class EmailLoginTests(TestCase):
    def test_login_accepts_email(self):
        User.objects.create_user(
            username='email-user',
            email='email-user@gawfinance.com',
            password='senha-forte-123',
        )

        response = self.client.post(reverse('login'), {
            'email': 'email-user@gawfinance.com',
            'password': 'senha-forte-123',
        })

        self.assertRedirects(response, '/')

    def test_login_rejects_invalid_email(self):
        response = self.client.post(reverse('login'), {
            'email': 'inválido@gawfinance.com',
            'password': 'senha-forte-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)


class AccountFlowTests(TestCase):
    def test_public_signup_is_disabled(self):
        response = self.client.get('/accounts/create/')

        self.assertEqual(response.status_code, 404)
        with self.assertRaises(NoReverseMatch):
            reverse('account_create')

    def test_bank_list_only_shows_authenticated_user_records(self):
        user_one = User.objects.create_user(username='20001', password='senha-1')
        user_two = User.objects.create_user(username='20002', password='senha-2')

        Bank.objects.create(user=user_one, name='Banco A', account_type='Corrente', agency=1, account=11)
        Bank.objects.create(user=user_two, name='Banco B', account_type='Corrente', agency=2, account=22)

        self.client.force_login(user_one)
        response = self.client.get(reverse('bank_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Banco A')
        self.assertNotContains(response, 'Banco B')


class OwnerInviteTests(TestCase):
    def test_create_owner_invite_command_creates_one_time_token(self):
        output = io.StringIO()
        call_command(
            'create_owner_invite',
            '--email',
            'owner@gawfinance.com',
            '--base-url',
            'http://testserver',
            stdout=output,
        )

        invite = Invite.objects.get(email='owner@gawfinance.com')
        self.assertTrue(invite.is_valid)
        self.assertTrue(invite.is_superuser)
        self.assertIn('/invite/', output.getvalue())
        self.assertIn(invite.token_hash, [Invite.hash_token(token) for token in re.findall(
            r'/invite/([^/\s]+)',
            output.getvalue(),
        )])

    def test_invite_accept_creates_superuser_and_account(self):
        token = Invite.generate_token()
        invite = Invite.objects.create(
            email='owner@gawfinance.com',
            token_hash=Invite.hash_token(token),
            is_superuser=True,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(
            reverse('invite_accept', kwargs={'token': token}),
            data={
                'name': 'Guilherme',
                'password': 'senha-forte-123',
                'confirm_password': 'senha-forte-123',
            },
        )

        user = User.objects.get(username='Guilherme')
        account = Account.objects.get(user=user)
        invite.refresh_from_db()

        self.assertRedirects(response, reverse('mfa_setup'))
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(account.name, 'Guilherme')
        self.assertTrue(invite.is_used)
        self.assertFalse(invite.is_valid)

    def test_invite_accept_creates_default_categories(self):
        token = Invite.generate_token()
        invite = Invite.objects.create(
            email='owner@gawfinance.com',
            token_hash=Invite.hash_token(token),
            is_superuser=True,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(
            reverse('invite_accept', kwargs={'token': token}),
            data={
                'name': 'Guilherme',
                'password': 'senha-forte-123',
                'confirm_password': 'senha-forte-123',
            },
        )

        user = User.objects.get(username='Guilherme')
        categories = list(
            Category.objects.filter(user=user).values_list('name', flat=True),
        )

        self.assertRedirects(response, reverse('mfa_setup'))
        self.assertEqual(sorted(categories), sorted(DEFAULT_CATEGORY_NAMES))

    def test_expired_invite_cannot_be_used(self):
        token = Invite.generate_token()
        Invite.objects.create(
            email='owner@gawfinance.com',
            token_hash=Invite.hash_token(token),
            is_superuser=True,
            expires_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(reverse('invite_accept', kwargs={'token': token}))

        self.assertEqual(response.status_code, 410)
        self.assertFalse(User.objects.filter(email='owner@gawfinance.com').exists())

    def test_used_invite_cannot_be_used(self):
        token = Invite.generate_token()
        Invite.objects.create(
            email='owner@gawfinance.com',
            token_hash=Invite.hash_token(token),
            is_superuser=True,
            expires_at=timezone.now() + timedelta(days=7),
            used_at=timezone.now(),
        )

        response = self.client.get(reverse('invite_accept', kwargs={'token': token}))

        self.assertEqual(response.status_code, 410)
        self.assertFalse(User.objects.filter(email='owner@gawfinance.com').exists())


class MFAFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner-mfa',
            email='owner-mfa@gawfinance.com',
            password='senha-forte-123',
            is_staff=True,
            is_superuser=True,
        )

    def _login(self):
        self.client.force_login(self.user)

    def _create_confirmed_setup(self):
        return MFASetup.objects.create(
            user=self.user,
            secret=pyotp.random_base32(),
            confirmed_at=timezone.now(),
        )

    def test_superuser_without_mfa_is_redirected_to_setup(self):
        self._login()
        response = self.client.get('/')

        self.assertRedirects(response, reverse('mfa_setup'))

    def test_admin_requires_mfa(self):
        self._login()
        response = self.client.get('/admin/')

        self.assertRedirects(response, reverse('mfa_setup'))

    def test_mfa_setup_generates_qr_and_recovery_codes(self):
        self._login()
        setup = MFASetup.objects.create(user=self.user, secret=pyotp.random_base32())

        response = self.client.get(reverse('mfa_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data:image/png;base64,')

        code = pyotp.TOTP(setup.secret).now()
        response = self.client.post(reverse('mfa_setup'), {'code': code})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'códigos de recuperação')
        setup.refresh_from_db()
        self.assertIsNotNone(setup.confirmed_at)
        self.assertEqual(RecoveryCode.objects.filter(user=self.user).count(), 8)
        self.assertTrue(self.client.session.get('mfa_verified'))

    def test_mfa_verify_accepts_totp_code(self):
        self._login()
        setup = self._create_confirmed_setup()

        response = self.client.post(reverse('mfa_verify'), {
            'code': pyotp.TOTP(setup.secret).now(),
        })

        self.assertRedirects(response, '/')
        self.assertTrue(self.client.session.get('mfa_verified'))

    def test_mfa_verify_accepts_recovery_code_once(self):
        self._login()
        self._create_confirmed_setup()
        recovery_code = RecoveryCode.generate_code()
        RecoveryCode.objects.create(
            user=self.user,
            code_hash=RecoveryCode.hash_code(recovery_code),
        )

        response = self.client.post(reverse('mfa_verify'), {'code': recovery_code})
        self.assertRedirects(response, '/')
        self.assertTrue(self.client.session.get('mfa_verified'))

        other_client = Client()
        other_client.force_login(self.user)
        response = other_client.post(reverse('mfa_verify'), {'code': recovery_code})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Código inválido')
        self.assertFalse(other_client.session.get('mfa_verified'))

    def test_mfa_rejects_invalid_totp(self):
        self._login()
        self._create_confirmed_setup()

        response = self.client.post(reverse('mfa_verify'), {'code': '000000'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Código inválido')
        self.assertFalse(self.client.session.get('mfa_verified'))


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='troca-senha',
            email='troca-senha@gawfinance.com',
            password='senha-atual-123',
        )
        self.client.force_login(self.user)
        Account.objects.get_or_create(user=self.user)

    def test_anonymous_is_redirected_to_login(self):
        anon_client = Client()
        response = anon_client.get(reverse('password_change'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_done_page_requires_login(self):
        anon_client = Client()
        response = anon_client.get(reverse('password_change_done'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_page_renders_the_three_fields(self):
        response = self.client.get(reverse('password_change'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Senha atual')
        self.assertContains(response, 'Nova senha')
        self.assertContains(response, 'Repetir nova senha')

    def test_rejects_wrong_current_password(self):
        response = self.client.post(reverse('password_change'), {
            'old_password': 'senha-errada',
            'new_password1': 'nova-senha-forte-456',
            'new_password2': 'nova-senha-forte-456',
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('senha-atual-123'))

    def test_rejects_mismatched_confirmation(self):
        response = self.client.post(reverse('password_change'), {
            'old_password': 'senha-atual-123',
            'new_password1': 'nova-senha-forte-456',
            'new_password2': 'outra-senha-789',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Os dois campos de senha não correspondem.')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('senha-atual-123'))

    def test_changes_password_and_redirects_to_done(self):
        response = self.client.post(reverse('password_change'), {
            'old_password': 'senha-atual-123',
            'new_password1': 'nova-senha-forte-456',
            'new_password2': 'nova-senha-forte-456',
        })

        self.assertRedirects(response, reverse('password_change_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nova-senha-forte-456'))
