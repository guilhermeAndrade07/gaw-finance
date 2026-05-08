from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from banks.models import Bank


class AccountFlowTests(TestCase):
    def test_account_create_view_creates_user_and_account(self):
        response = self.client.post(
            reverse('account_create'),
            data={
                'name': 'Guilherme',
                'email': 'guilherme@example.com',
                'password': 'senha-forte-123',
                'confirm_password': 'senha-forte-123',
            },
        )

        account = Account.objects.get(user__username='Guilherme')
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='Guilherme', email='guilherme@example.com').exists())
        self.assertEqual(account.name, 'Guilherme')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_account_create_view_requires_password_confirmation(self):
        response = self.client.post(
            reverse('account_create'),
            data={
                'name': 'Conta Invalida',
                'email': 'invalida@example.com',
                'password': 'senha-forte-123',
                'confirm_password': 'senha-diferente-123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A confirmacao de senha nao confere.')
        self.assertFalse(User.objects.filter(username='Conta Invalida').exists())

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
