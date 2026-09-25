from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from banks.services import reconcile_bank_balances
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
