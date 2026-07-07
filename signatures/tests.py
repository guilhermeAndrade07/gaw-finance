import calendar
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from banks.models import Bank
from categories.models import Category
from payment.models import CreditCard, Payment
from signatures.models import Signature
from signatures.services import generate_signature_charges


class SignatureChargeTests(TestCase):
    _DEFAULT_CARD = object()

    def setUp(self):
        self.user = User.objects.create_user(username='user-sig', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco A',
            account_type='Corrente',
            agency=1,
            account=11,
        )
        self.card = CreditCard.objects.create(
            user=self.user,
            bank=self.bank,
            name='Cartao A',
            credit_limit=Decimal('1000.00'),
        )
        self.category = Category.objects.create(user=self.user, name='Streaming')
        self.today = date.today()

    def _create_signature(self, billing_day=None, is_active=True, credit_card=_DEFAULT_CARD):
        return Signature.objects.create(
            user=self.user,
            name='Netflix',
            description='Assinatura mensal',
            value=Decimal('39.90'),
            billing_day=billing_day or self.today.day,
            is_active=is_active,
            credit_card=self.card if credit_card is SignatureChargeTests._DEFAULT_CARD else credit_card,
            category=self.category,
        )

    def test_generate_charges_creates_payment(self):
        self._create_signature(billing_day=self.today.day)
        generate_signature_charges()

        payment = Payment.objects.filter(user=self.user, card=self.card).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.value, Decimal('39.90'))
        self.assertEqual(payment.parcelas, 1)
        self.assertFalse(payment.paid)
        self.assertTrue(payment.name.startswith('Assinatura: Netflix'))
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        expected_day = min(self.today.day, last_day)
        self.assertEqual(payment.date_payment, date(self.today.year, self.today.month, expected_day))

    def test_generate_charges_idempotent(self):
        self._create_signature(billing_day=self.today.day)
        generate_signature_charges()
        generate_signature_charges()
        self.assertEqual(Payment.objects.filter(user=self.user, card=self.card).count(), 1)

    def test_inactive_signature_no_charge(self):
        self._create_signature(billing_day=self.today.day, is_active=False)
        generate_signature_charges()
        self.assertFalse(Payment.objects.filter(user=self.user, card=self.card).exists())

    def test_signature_without_card_no_charge(self):
        self._create_signature(billing_day=self.today.day, credit_card=None)
        generate_signature_charges()
        self.assertFalse(Payment.objects.filter(user=self.user).exists())

    def test_charge_date_is_billing_day_not_today(self):
        billing_day = max(self.today.day - 5, 1)
        self._create_signature(billing_day=billing_day)
        generate_signature_charges()

        payment = Payment.objects.filter(user=self.user, card=self.card).first()
        self.assertIsNotNone(payment)
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        expected_day = min(billing_day, last_day)
        self.assertEqual(
            payment.date_payment,
            date(self.today.year, self.today.month, expected_day),
        )

    def test_billing_day_clamped_for_short_month(self):
        self._create_signature(billing_day=31)
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        if self.today.day < last_day:
            self.skipTest('Dia atual ainda nao alcancou o fim do mes curto')

        generate_signature_charges()
        payment = Payment.objects.filter(user=self.user, card=self.card).first()
        self.assertIsNotNone(payment)
        self.assertEqual(
            payment.date_payment,
            date(self.today.year, self.today.month, last_day),
        )

    def test_billing_day_not_reached_no_charge(self):
        future_day = self.today.day + 1
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        if future_day > last_day:
            self.skipTest('Nao ha dia futuro valido neste mes')
        self._create_signature(billing_day=future_day)
        generate_signature_charges()
        self.assertFalse(Payment.objects.filter(user=self.user, card=self.card).exists())

    def test_signature_list_shows_credit_card(self):
        self._create_signature(billing_day=self.today.day)
        self.client.force_login(self.user)
        response = self.client.get(reverse('signature_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cartao A')
        self.assertContains(response, 'Cartao')

    def test_signature_create_requires_credit_card(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('signature_create'),
            {
                'name': 'Spotify',
                'description': 'Musica',
                'value': '19.90',
                'billing_day': '5',
                'is_active': 'on',
                'category': self.category.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Signature.objects.filter(user=self.user, name='Spotify').exists())

    def test_signature_create_with_credit_card_succeeds(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('signature_create'),
            {
                'name': 'Spotify',
                'description': 'Musica',
                'value': '19.90',
                'billing_day': '5',
                'is_active': 'on',
                'credit_card': self.card.id,
                'category': self.category.id,
            },
        )
        self.assertRedirects(response, reverse('signature_list'))
        sig = Signature.objects.filter(user=self.user, name='Spotify').first()
        self.assertIsNotNone(sig)
        self.assertEqual(sig.credit_card_id, self.card.id)

    def test_middleware_triggers_charge_on_request(self):
        self._create_signature(billing_day=self.today.day)
        self.client.force_login(self.user)
        self.client.get(reverse('signature_list'))
        self.assertTrue(Payment.objects.filter(user=self.user, card=self.card).exists())
