from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from banks.models import Bank
from categories.models import Category
from payment.models import CreditCard, Payment


class CreditCardPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user-one', password='pass123')
        self.other_user = User.objects.create_user(username='user-two', password='pass123')
        self.category = Category.objects.create(user=self.user, name='Mercado')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco A',
            account_type='Corrente',
            agency=1,
            account=11,
        )
        self.other_bank = Bank.objects.create(
            user=self.other_user,
            name='Banco B',
            account_type='Corrente',
            agency=2,
            account=22,
        )
        self.card = CreditCard.objects.create(
            user=self.user,
            bank=self.bank,
            name='Cartao A',
            credit_limit=Decimal('1000.00'),
        )
        self.other_card = CreditCard.objects.create(
            user=self.other_user,
            bank=self.other_bank,
            name='Cartao B',
            credit_limit=Decimal('500.00'),
        )

    def test_payment_list_filters_by_card_and_reports_credit_values(self):
        Payment.objects.create(
            user=self.user,
            card=self.card,
            name='Compra Cartao A',
            category=self.category,
            date_payment=date(2026, 5, 10),
            value=Decimal('120.00'),
        )
        Payment.objects.create(
            user=self.user,
            name='Compra Sem Cartao',
            category=self.category,
            date_payment=date(2026, 5, 10),
            value=Decimal('50.00'),
        )
        Payment.objects.create(
            user=self.user,
            card=self.card,
            name='Compra Paga',
            category=self.category,
            date_payment=date(2026, 5, 10),
            value=Decimal('30.00'),
            paid=True,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('payment_list'), {'card': self.card.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Compra Cartao A')
        self.assertNotContains(response, 'Compra Sem Cartao')
        self.assertNotContains(response, 'Compra Paga')
        self.assertEqual(response.context['payment_total'], Decimal('120.00'))
        self.assertEqual(response.context['credit_used'], Decimal('120.00'))
        self.assertEqual(response.context['credit_available'], Decimal('880.00'))

        response = self.client.get(reverse('payment_list'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['selected_card'])
        self.assertNotContains(response, 'Compra Cartao A')
        self.assertNotContains(response, 'Compra Sem Cartao')
        self.assertEqual(response.context['payment_total'], 0)
        self.assertEqual(response.context['credit_used'], Decimal('0.00'))
        self.assertEqual(response.context['credit_available'], Decimal('0.00'))

        response = self.client.get(reverse('payment_list'), {'card': 'unassigned'})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['selected_card'])
        self.assertNotContains(response, 'Compra Sem Cartao')
        self.assertNotContains(response, 'Compra Cartao A')
        self.assertEqual(response.context['payment_total'], 0)
        self.assertEqual(response.context['credit_used'], Decimal('0.00'))
        self.assertEqual(response.context['credit_available'], Decimal('0.00'))

    def test_credit_available_never_goes_negative(self):
        Payment.objects.create(
            user=self.user,
            card=self.card,
            name='Compra Acima do Limite',
            category=self.category,
            date_payment=date(2026, 5, 10),
            value=Decimal('1200.00'),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('payment_list'), {'card': self.card.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['credit_used'], Decimal('1200.00'))
        self.assertEqual(response.context['credit_available'], Decimal('0.00'))

    def test_payment_creation_requires_card(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment_create'),
            {
                'name': 'Compra sem cartao',
                'description': 'Nao deve salvar',
                'category': self.category.id,
                'date_payment': '2026-05-10',
                'value': '100.00',
                'parcelas': '1',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user, name='Compra sem cartao').exists())

    def test_installment_creation_keeps_selected_card(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment_create'),
            {
                'card': self.card.id,
                'name': 'Notebook',
                'description': 'Compra parcelada',
                'category': self.category.id,
                'date_payment': '2026-05-10',
                'value': '100.00',
                'parcelas': '2',
            },
        )

        self.assertRedirects(response, f"{reverse('payment_list')}?card={self.card.id}")
        payments = Payment.objects.filter(user=self.user, card=self.card).order_by('date_payment')
        self.assertEqual(payments.count(), 2)
        self.assertEqual(payments[0].name, 'Notebook (1/2)')
        self.assertEqual(payments[0].value, Decimal('50.00'))
        self.assertEqual(payments[1].name, 'Notebook (2/2)')
        self.assertEqual(payments[1].value, Decimal('50.00'))

    def test_payment_create_prefills_selected_card_from_querystring(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment_create'), {'card': self.card.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['card'], str(self.card.id))

    def test_credit_card_limit_cannot_be_negative(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('credit_card_create'),
            {
                'name': 'Cartao Negativo',
                'bank': self.bank.id,
                'credit_limit': '-1.00',
                'active': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CreditCard.objects.filter(user=self.user, name='Cartao Negativo').exists())

    def test_credit_card_list_is_user_scoped(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('credit_card_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cartao A')
        self.assertNotContains(response, 'Cartao B')
