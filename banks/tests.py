from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction as db_transaction
from django.test import TestCase
from django.urls import reverse

from banks.services import reconcile_bank_balances, set_main_bank, ensure_main_bank, user_has_main_bank
from inflows.models import Inflow
from outflows.models import Outflow

from .models import Bank


class BankBalanceReconciliationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bank-reconcile-user', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco reconciliacao',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )

    def test_reconcile_bank_balances_repairs_stored_balance(self):
        Inflow.objects.create(user=self.user, title='Entrada', bank=self.bank, value=Decimal('50.00'))
        Outflow.objects.create(user=self.user, title='Saida', bank=self.bank, value=Decimal('20.00'))
        Bank.objects.filter(pk=self.bank.pk).update(balance=Decimal('999.00'))

        updated = reconcile_bank_balances()

        self.bank.refresh_from_db()
        self.assertEqual(updated, [{'id': self.bank.pk, 'balance': '130.00'}])
        self.assertEqual(self.bank.balance, Decimal('130.00'))
        self.assertEqual(self.bank.current_balance, Decimal('130.00'))

    def test_reconcile_bank_balances_does_not_change_consistent_bank(self):
        updated = reconcile_bank_balances()

        self.assertEqual(updated, [])
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))
        self.assertEqual(self.bank.current_balance, Decimal('100.00'))


class BankMainFlagTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bank-main-user', password='pass123')
        self.bank_one = Bank.objects.create(
            user=self.user,
            name='Banco A',
            account_type='Corrente',
            agency=1,
            account=11,
        )
        self.bank_two = Bank.objects.create(
            user=self.user,
            name='Banco B',
            account_type='Poupanca',
            agency=2,
            account=22,
        )
        self.other_user = User.objects.create_user(username='bank-main-other', password='pass123')

    def test_set_main_bank_promotes_selected_and_demotes_others(self):
        self.bank_two.is_main = True
        self.bank_two.save(update_fields=['is_main'])

        set_main_bank(user=self.user, bank=self.bank_one)

        self.bank_one.refresh_from_db()
        self.bank_two.refresh_from_db()
        self.assertTrue(self.bank_one.is_main)
        self.assertFalse(self.bank_two.is_main)

    def test_main_bank_is_isolated_per_user(self):
        set_main_bank(user=self.user, bank=self.bank_one)

        other_bank = Bank.objects.create(
            user=self.other_user,
            name='Banco C',
            account_type='Corrente',
            agency=3,
            account=33,
        )
        set_main_bank(user=self.other_user, bank=other_bank)

        self.bank_one.refresh_from_db()
        other_bank.refresh_from_db()
        self.assertTrue(self.bank_one.is_main)
        self.assertTrue(other_bank.is_main)

    def test_ensure_main_bank_promotes_first_bank(self):
        self.assertFalse(user_has_main_bank(self.user))

        ensure_main_bank(self.user, self.bank_two)

        self.assertTrue(user_has_main_bank(self.user))
        self.bank_two.refresh_from_db()
        self.assertTrue(self.bank_two.is_main)

    def test_ensure_main_bank_keeps_existing_main(self):
        set_main_bank(self.user, self.bank_one)

        ensure_main_bank(self.user, self.bank_two)

        self.bank_one.refresh_from_db()
        self.bank_two.refresh_from_db()
        self.assertTrue(self.bank_one.is_main)
        self.assertFalse(self.bank_two.is_main)

    def test_unique_main_bank_constraint_enforced(self):
        """A constraint do banco de dados protege contra mais de um principal."""
        self.bank_one.is_main = True
        self.bank_one.save(update_fields=['is_main'])
        self.bank_two.is_main = True

        with self.assertRaises(IntegrityError):
            with db_transaction.atomic():
                self.bank_two.save()

        banks_main = Bank.objects.filter(user=self.user, is_main=True)
        self.assertEqual(banks_main.count(), 1)


class BankMainOrderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bank-order-user', password='pass123')

    def test_main_bank_appears_first_in_ordering(self):
        secondary = Bank.objects.create(user=self.user, name='Zeta Bank', account_type='Corrente', agency=3, account=33)
        main = Bank.objects.create(
            user=self.user,
            name='Alfa Antigo',
            account_type='Corrente',
            agency=1,
            account=10,
            is_main=True,
        )

        ordered = list(Bank.objects.filter(user=self.user).values_list('id', flat=True))

        self.assertEqual(ordered, [main.pk, secondary.pk])


class BankSetMainViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bank-view-user', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco view',
            account_type='Corrente',
            agency=1,
            account=11,
        )
        self.other_user_bank = Bank.objects.create(
            name='Banco alheio',
            account_type='Corrente',
            agency=9,
            account=99,
        )
        self.url = reverse('bank_set_main', args=[self.bank.pk])

    def test_set_main_requires_post(self):
        self.client.login(username='bank-view-user', password='pass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_set_main_requires_login(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)

    def test_set_main_marks_bank_as_principal(self):
        self.client.login(username='bank-view-user', password='pass123')
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.bank.refresh_from_db()
        self.assertTrue(self.bank.is_main)

    def test_set_main_cannot_affect_bank_of_other_user(self):
        self.client.login(username='bank-view-user', password='pass123')
        url_outro = reverse('bank_set_main', args=[self.other_user_bank.pk])
        response = self.client.post(url_outro)

        self.assertEqual(response.status_code, 404)
        self.other_user_bank.refresh_from_db()
        self.assertFalse(self.other_user_bank.is_main)
