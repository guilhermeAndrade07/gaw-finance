from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from banks.models import Bank
from categories.models import Category
from payment.models import CreditCard, Invoice, Payment
from payment.services import (
    backfill_invoices,
    close_past_invoices,
)


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
            closing_day=20,
            due_day=10,
        )
        self.other_card = CreditCard.objects.create(
            user=self.other_user,
            bank=self.other_bank,
            name='Cartao B',
            credit_limit=Decimal('500.00'),
            closing_day=20,
            due_day=10,
        )

    def test_payment_list_redirects_with_querystring(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment_list'), {'card': self.card.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('invoice_list'), response['Location'])
        self.assertIn(f'card={self.card.id}', response['Location'])

    def test_invoice_list_reports_credit_values(self):
        Payment.objects.create(
            user=self.user,
            card=self.card,
            name='Compra Cartao A',
            category=self.category,
            date_payment=date(2026, 5, 10),
            value=Decimal('120.00'),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['credit_used'], Decimal('120.00'))
        self.assertEqual(response.context['credit_available'], Decimal('880.00'))

    def test_invoice_list_credit_available_never_goes_negative(self):
        Payment.objects.create(
            user=self.user,
            card=self.card,
            name='Compra Acima do Limite',
            category=self.category,
            date_payment=date(2026, 5, 10),
            value=Decimal('1200.00'),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['credit_used'], Decimal('1200.00'))
        self.assertEqual(response.context['credit_available'], Decimal('0.00'))

    def test_payment_creation_requires_card(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment_create'),
            {
                'name': 'Compra sem cartao',
                'category': self.category.id,
                'date_payment': '10/05/2026',
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
                'category': self.category.id,
                'date_payment': '10/05/2026',
                'value': '100.00',
                'parcelas': '2',
            },
        )

        self.assertRedirects(response, f"{reverse('invoice_list')}?card={self.card.id}")
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


class InvoiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user-inv', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco X',
            account_type='Corrente',
            agency=1,
            account=11,
        )
        self.category = Category.objects.create(user=self.user, name='Mercado')
        self.card = CreditCard.objects.create(
            user=self.user,
            bank=self.bank,
            name='Cartao X',
            credit_limit=Decimal('2000.00'),
            closing_day=20,
            due_day=10,
        )
        self.card_no_cycle = CreditCard.objects.create(
            user=self.user,
            bank=self.bank,
            name='Cartao Sem Ciclo',
            credit_limit=Decimal('1000.00'),
        )

    def _create_payment(self, card, day, month, year, value=Decimal('100.00')):
        return Payment.objects.create(
            user=self.user,
            card=card,
            name=f'Compra {day}/{month}',
            category=self.category,
            date_payment=date(year, month, day),
            value=value,
            parcelas=1,
        )

    def test_invoice_assignment_before_closing_day(self):
        payment = self._create_payment(self.card, day=15, month=6, year=2026)
        self.assertIsNotNone(payment.invoice_id)
        self.assertEqual(payment.invoice.closing_date, date(2026, 6, 20))

    def test_invoice_assignment_on_closing_day(self):
        payment = self._create_payment(self.card, day=20, month=6, year=2026)
        self.assertEqual(payment.invoice.closing_date, date(2026, 7, 20))

    def test_invoice_assignment_after_closing_day(self):
        payment = self._create_payment(self.card, day=25, month=6, year=2026)
        self.assertEqual(payment.invoice.closing_date, date(2026, 7, 20))

    def test_invoice_reused_for_same_cycle(self):
        p1 = self._create_payment(self.card, day=5, month=6, year=2026)
        p2 = self._create_payment(self.card, day=15, month=6, year=2026)
        self.assertEqual(p1.invoice_id, p2.invoice_id)
        self.assertEqual(Invoice.objects.filter(card=self.card).count(), 1)

    def test_invoice_due_date_when_due_after_closing(self):
        card = CreditCard.objects.create(
            user=self.user, bank=self.bank, name='Card Due After',
            credit_limit=Decimal('1000.00'),
            closing_day=20, due_day=25,
        )
        payment = self._create_payment(card, day=10, month=6, year=2026)
        self.assertEqual(payment.invoice.closing_date, date(2026, 6, 20))
        self.assertEqual(payment.invoice.due_date, date(2026, 6, 25))

    def test_invoice_due_date_when_due_before_closing(self):
        card = CreditCard.objects.create(
            user=self.user, bank=self.bank, name='Card Due Before',
            credit_limit=Decimal('1000.00'),
            closing_day=20, due_day=10,
        )
        payment = self._create_payment(card, day=10, month=6, year=2026)
        self.assertEqual(payment.invoice.closing_date, date(2026, 6, 20))
        self.assertEqual(payment.invoice.due_date, date(2026, 7, 10))

    def test_close_past_invoices(self):
        invoice = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2020, 1, 20),
            due_date=date(2020, 2, 10),
            status=Invoice.OPEN,
        )
        close_past_invoices()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.CLOSED)

    def test_invoice_pay_marks_all_payments(self):
        invoice = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 6, 20),
            due_date=date(2026, 7, 10),
            status=Invoice.CLOSED,
        )
        p1 = self._create_payment(self.card, day=5, month=6, year=2026)
        p2 = self._create_payment(self.card, day=10, month=6, year=2026)
        p1.invoice = invoice
        p2.invoice = invoice
        p1.save()
        p2.save()

        self.client.force_login(self.user)
        response = self.client.post(reverse('invoice_pay', kwargs={'pk': invoice.id}))
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.PAID)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertTrue(p1.paid)
        self.assertTrue(p2.paid)

    def test_invoice_list_filters_by_card(self):
        Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 6, 20),
            due_date=date(2026, 7, 10),
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fatura Junho 2026')

        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Fatura Junho 2026')

    def test_payment_without_closing_day_has_no_invoice(self):
        payment = self._create_payment(self.card_no_cycle, day=10, month=6, year=2026)
        self.assertIsNone(payment.invoice_id)

    def test_installment_assigns_each_to_invoice(self):
        from django.urls import reverse
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment_create'),
            {
                'card': self.card.id,
                'name': 'Notebook 3x',
                'category': self.category.id,
                'date_payment': '15/06/2026',
                'value': '300.00',
                'parcelas': '3',
            },
        )
        self.assertRedirects(response, f"{reverse('invoice_list')}?card={self.card.id}")
        payments = Payment.objects.filter(user=self.user, card=self.card).order_by('date_payment')
        self.assertEqual(payments.count(), 3)
        self.assertEqual(Invoice.objects.filter(card=self.card).count(), 3)
        for p in payments:
            self.assertIsNotNone(p.invoice_id)

    def test_backfill_assigns_existing_payments(self):
        payment = Payment.objects.create(
            user=self.user,
            card=self.card,
            name='Compra antiga',
            category=self.category,
            date_payment=date(2026, 6, 5),
            value=Decimal('50.00'),
            parcelas=1,
            invoice=None,
        )
        # Forca invoice=None bypassando o signal via update
        Payment.objects.filter(pk=payment.pk).update(invoice=None)
        payment.refresh_from_db()
        self.assertIsNone(payment.invoice_id)

        backfill_invoices()
        payment.refresh_from_db()
        self.assertIsNotNone(payment.invoice_id)
        self.assertEqual(payment.invoice.closing_date, date(2026, 6, 20))

    def test_invoice_detail_shows_payments(self):
        invoice = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 6, 20),
            due_date=date(2026, 7, 10),
            status=Invoice.CLOSED,
        )
        p1 = self._create_payment(self.card, day=5, month=6, year=2026)
        p1.invoice = invoice
        p1.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_detail', kwargs={'pk': invoice.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Compra 5/6')
        self.assertContains(response, 'R$ 100,00')

    def test_payment_list_redirects_to_invoice_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('invoice_list'), response['Location'])

    def test_payment_list_redirect_preserves_querystring(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment_list'), {'card': self.card.id, 'name': 'foo'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'card={self.card.id}', response['Location'])
        self.assertIn('name=foo', response['Location'])

    def test_invoice_list_shows_warning_for_card_without_closing_day(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card_no_cycle.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configure o')

    def test_invoice_list_shows_accordion_with_payments(self):
        invoice = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 6, 20),
            due_date=date(2026, 7, 10),
            status=Invoice.OPEN,
        )
        p1 = self._create_payment(self.card, day=5, month=6, year=2026, value=Decimal('50.00'))
        p1.invoice = invoice
        p1.save()
        p2 = self._create_payment(self.card, day=10, month=6, year=2026, value=Decimal('30.00'))
        p2.invoice = invoice
        p2.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Compra 5/6')
        self.assertContains(response, 'Compra 10/6')

    def test_invoice_list_search_filters_by_purchase_name(self):
        inv1 = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 6, 20), due_date=date(2026, 7, 10),
        )
        inv2 = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 7, 20), due_date=date(2026, 8, 10),
        )
        p1 = self._create_payment(self.card, day=5, month=6, year=2026)
        p1.name = 'Netflix'
        p1.invoice = inv1
        p1.save()
        p2 = self._create_payment(self.card, day=5, month=7, year=2026)
        p2.name = 'Spotify'
        p2.invoice = inv2
        p2.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card.id, 'name': 'Netflix'})
        self.assertEqual(response.status_code, 200)
        invoices = response.context['invoices']
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].id, inv1.id)

    def test_invoice_list_show_hidden_displays_paid_invoices(self):
        paid_inv = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 6, 20), due_date=date(2026, 7, 10),
            status=Invoice.PAID,
        )
        open_inv = Invoice.objects.create(
            user=self.user, card=self.card,
            closing_date=date(2026, 7, 20), due_date=date(2026, 8, 10),
            status=Invoice.OPEN,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice_list'), {'card': self.card.id, 'show_hidden': '1'})
        self.assertEqual(response.status_code, 200)
        invoice_ids = [inv.id for inv in response.context['invoices']]
        self.assertIn(paid_inv.id, invoice_ids)
        self.assertNotIn(open_inv.id, invoice_ids)

        response = self.client.get(reverse('invoice_list'), {'card': self.card.id})
        invoice_ids = [inv.id for inv in response.context['invoices']]
        self.assertIn(open_inv.id, invoice_ids)
        self.assertNotIn(paid_inv.id, invoice_ids)

    def test_payment_create_redirects_to_invoice_list(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment_create'),
            {
                'card': self.card.id,
                'name': 'Compra Teste',
                'category': self.category.id,
                'date_payment': '15/06/2026',
                'value': '100.00',
                'parcelas': '1',
            },
        )
        self.assertRedirects(response, f"{reverse('invoice_list')}?card={self.card.id}")


class PaymentPaidToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user-toggle', password='pass123')
        self.other_user = User.objects.create_user(username='user-other-toggle', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user, name='Banco T', account_type='Corrente', agency=1, account=11,
        )
        self.category = Category.objects.create(user=self.user, name='Mercado')
        self.card = CreditCard.objects.create(
            user=self.user, bank=self.bank, name='Cartao T',
            credit_limit=Decimal('1000.00'), closing_day=20, due_day=10,
        )
        self.payment = Payment.objects.create(
            user=self.user, card=self.card, name='Compra Agosto',
            category=self.category, date_payment=date(2026, 8, 5),
            value=Decimal('80.00'), parcelas=1,
        )

    def test_mark_paid_sets_paid_true(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('payment_mark_paid', kwargs={'pk': self.payment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.payment.refresh_from_db()
        self.assertTrue(self.payment.paid)

    def test_mark_unpaid_sets_paid_false(self):
        self.payment.paid = True
        self.payment.save(update_fields=['paid'])
        self.client.force_login(self.user)
        response = self.client.post(reverse('payment_mark_unpaid', kwargs={'pk': self.payment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.payment.refresh_from_db()
        self.assertFalse(self.payment.paid)

    def test_toggle_round_trip_paid_then_unpaid(self):
        self.client.force_login(self.user)
        self.client.post(reverse('payment_mark_paid', kwargs={'pk': self.payment.id}))
        self.payment.refresh_from_db()
        self.assertTrue(self.payment.paid)
        self.client.post(reverse('payment_mark_unpaid', kwargs={'pk': self.payment.id}))
        self.payment.refresh_from_db()
        self.assertFalse(self.payment.paid)

    def test_mark_paid_is_user_scoped(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('payment_mark_paid', kwargs={'pk': self.payment.id}))
        self.assertEqual(response.status_code, 404)
        self.payment.refresh_from_db()
        self.assertFalse(self.payment.paid)
