from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from banks.models import Bank
from inflows.models import Inflow


class InflowBalanceSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user-in', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Itau',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )

    def _create_inflow(self, value=Decimal('50.00')):
        return Inflow.objects.create(
            user=self.user,
            title='Entrada',
            bank=self.bank,
            value=value,
        )

    def test_create_inflow_adds_bank_balance(self):
        self._create_inflow(value=Decimal('40.00'))

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('140.00'))

    def test_delete_inflow_subtracts_bank_balance(self):
        inflow = self._create_inflow(value=Decimal('40.00'))
        inflow.delete()

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))

    def test_edit_inflow_adjusts_bank_balance(self):
        inflow = self._create_inflow(value=Decimal('40.00'))
        inflow.value = Decimal('70.00')
        inflow.save()

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('170.00'))
