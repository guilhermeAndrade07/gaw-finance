from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from app.mixins import UserScopedSerializerMixin
from banks.models import Bank
from categories.models import Category
from goals.models import MonthlyGoal
from investments.models import InvestmentAsset, InvestmentMovement
from investments.serializers import InvestmentMovementSerializer
from payment.forms import PaymentForm
from payment.models import CreditCard, Payment
from payment.serializers import InvoiceSerializer
from signatures.models import Signature


class OwnershipIsolationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ownership-user', password='pass123')
        self.other_user = User.objects.create_user(username='ownership-other', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco do usuario',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('1000.00'),
            balance=Decimal('1000.00'),
        )
        self.other_bank = Bank.objects.create(
            user=self.other_user,
            name='Banco de outro usuario',
            account_type='Corrente',
            agency=2,
            account=22,
        )
        self.category = Category.objects.create(user=self.user, name='Categoria do usuario')
        self.other_category = Category.objects.create(user=self.other_user, name='Categoria de outro usuario')
        self.card = CreditCard.objects.create(
            user=self.user,
            bank=self.bank,
            name='Cartao do usuario',
            credit_limit=Decimal('1000.00'),
        )
        self.other_card = CreditCard.objects.create(
            user=self.other_user,
            bank=self.other_bank,
            name='Cartao de outro usuario',
            credit_limit=Decimal('1000.00'),
        )
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

    def _request(self):
        request = APIRequestFactory().get('/')
        request.user = self.user
        return request

    def test_api_rejects_foreign_related_objects(self):
        cases = [
            (
                'inflow-create-list-api-view',
                {'title': 'Entrada', 'bank': self.other_bank.pk, 'value': '10.00'},
            ),
            (
                'outflow-create-list-api-view',
                {
                    'title': 'Saida',
                    'bank': self.bank.pk,
                    'category': self.other_category.pk,
                    'value': '10.00',
                },
            ),
            (
                'transfer-create-list-api-view',
                {
                    'title': 'Transferencia',
                    'source_bank': self.bank.pk,
                    'destination_bank': self.other_bank.pk,
                    'value': '10.00',
                },
            ),
            (
                'payment-create-list-api-view',
                {
                    'card': self.card.pk,
                    'name': 'Compra',
                    'category': self.other_category.pk,
                    'date_payment': '2026-01-10',
                    'value': '10.00',
                    'parcelas': 1,
                },
            ),
            (
                'signature-create-list-api-view',
                {
                    'name': 'Assinatura',
                    'value': '10.00',
                    'billing_day': 10,
                    'credit_card': self.card.pk,
                    'category': self.other_category.pk,
                },
            ),
            (
                'investment-create-list-api-view',
                {
                    'name': 'Ativo',
                    'asset_type': InvestmentAsset.CRYPTO,
                    'bank': self.other_bank.pk,
                },
            ),
            (
                'goal-create-list-api-view',
                {
                    'category': self.other_category.pk,
                    'value': '10.00',
                    'month': 1,
                    'year': 2026,
                },
            ),
        ]

        for url_name, payload in cases:
            with self.subTest(url_name=url_name):
                response = self.api_client.post(reverse(url_name), payload, format='json')
                self.assertEqual(response.status_code, 400)

        self.assertFalse(InvestmentAsset.objects.filter(name='Ativo').exists())
        self.assertFalse(MonthlyGoal.objects.filter(value=Decimal('10.00')).exists())
        self.assertFalse(Payment.objects.filter(name='Compra').exists())
        self.assertFalse(Signature.objects.filter(name='Assinatura').exists())

    def test_read_only_invoice_serializer_rejects_foreign_card(self):
        serializer = InvoiceSerializer(
            data={
                'card': self.other_card.pk,
                'closing_date': '2026-01-20',
                'due_date': '2026-02-10',
            },
            context={'request': self._request()},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('card', serializer.errors)

    def test_investment_movement_serializer_rejects_foreign_asset(self):
        foreign_asset = InvestmentAsset.objects.create(
            user=self.other_user,
            bank=self.other_bank,
            name='Ativo de outro usuario',
            asset_type=InvestmentAsset.CRYPTO,
        )
        serializer = InvestmentMovementSerializer(
            data={
                'asset': foreign_asset.pk,
                'operation_type': InvestmentMovement.APPORTION,
                'value': '10.00',
                'movement_date': '2026-01-10',
            },
            context={'request': self._request()},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('asset', serializer.errors)

    def test_api_rejects_invalid_financial_values(self):
        cases = [
            (
                'inflow-create-list-api-view',
                {'title': 'Entrada', 'bank': self.bank.pk, 'value': '0.00'},
            ),
            (
                'outflow-create-list-api-view',
                {'title': 'Saida', 'bank': self.bank.pk, 'value': '-1.00'},
            ),
            (
                'payment-create-list-api-view',
                {
                    'card': self.card.pk,
                    'name': 'Compra',
                    'category': self.category.pk,
                    'date_payment': '2026-01-10',
                    'value': '10.00',
                    'parcelas': 61,
                },
            ),
            (
                'signature-create-list-api-view',
                {
                    'name': 'Assinatura',
                    'value': '0.00',
                    'billing_day': 10,
                    'credit_card': self.card.pk,
                },
            ),
            (
                'goal-create-list-api-view',
                {
                    'category': self.category.pk,
                    'value': '10.00',
                    'month': 1,
                    'year': 1999,
                },
            ),
        ]

        for url_name, payload in cases:
            with self.subTest(url_name=url_name):
                response = self.api_client.post(reverse(url_name), payload, format='json')
                self.assertEqual(response.status_code, 400)

    def test_payment_form_rejects_invalid_value_and_installments(self):
        form = PaymentForm(
            data={
                'card': self.card.pk,
                'name': 'Compra',
                'category': self.category.pk,
                'date_payment': '10/01/2026',
                'value': '0.00',
                'parcelas': 61,
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('value', form.errors)
        self.assertIn('parcelas', form.errors)

    def test_request_limits_are_configured(self):
        self.assertEqual(settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 2 * 1024 * 1024)
        self.assertEqual(settings.DATA_UPLOAD_MAX_NUMBER_FIELDS, 200)

    def test_database_constraint_rejects_non_positive_payment(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    user=self.user,
                    card=self.card,
                    name='Compra invalida',
                    category=self.category,
                    date_payment='2026-01-10',
                    value=Decimal('-1.00'),
                )

    def test_serializer_mixin_uses_authenticated_user(self):
        serializer = InvoiceSerializer(context={'request': self._request()})
        self.assertIsInstance(serializer, UserScopedSerializerMixin)
        self.assertEqual(serializer.fields['card'].queryset.count(), 1)
        self.assertEqual(serializer.fields['card'].queryset.first(), self.card)


class SecurityHeadersTests(TestCase):
    def test_security_headers_are_applied(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        csp = response.headers.get('Content-Security-Policy', '')
        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(response.headers.get('Cross-Origin-Opener-Policy'), 'same-origin')
        self.assertEqual(response.headers.get('Cross-Origin-Resource-Policy'), 'same-origin')
        self.assertIn('camera=()', response.headers.get('Permissions-Policy', ''))

    def test_login_does_not_load_remote_scripts(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'https://unpkg.com')
        self.assertNotContains(response, 'https://cdn.jsdelivr.net')

    def test_dashboard_does_not_load_remote_scripts(self):
        user = User.objects.create_user(username='dashboard-user', password='pass123')
        Bank.objects.create(
            user=user,
            name='Banco dashboard',
            account_type='Corrente',
            agency=1,
            account=11,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'https://unpkg.com')
        self.assertNotContains(response, 'https://cdn.jsdelivr.net')


class ReadinessCheckTests(TestCase):
    def test_readiness_check_returns_ok_when_dependencies_are_ready(self):
        from unittest import mock

        with mock.patch('app.views.Connection') as connection_mock:
            connection_mock.return_value.__enter__.return_value.ensure_connection.return_value = None

            response = self.client.get(reverse('readiness_check'))

        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()['ready'])
        self.assertTrue(response.json()['checks']['database'])
        self.assertTrue(response.json()['checks']['cache'])
        self.assertTrue(response.json()['checks']['broker'])

    def test_readiness_check_returns_503_when_broker_is_unavailable(self):
        from unittest import mock

        with mock.patch('app.views.Connection') as connection_mock:
            connection_mock.return_value.__enter__.return_value.ensure_connection.side_effect = Exception('broker down')

            response = self.client.get(reverse('readiness_check'))

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()['ready'])
        self.assertFalse(response.json()['checks']['broker'])


class ReportEscapingTests(TestCase):
    def test_report_cell_escapes_user_content(self):
        from reports.services import _cell

        cell = _cell('<img src=x onerror=alert(1)>')
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', cell.text)
