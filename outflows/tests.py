from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from banks.models import Bank
from categories.models import Category
from inflows.models import Inflow
from outflows.forms import OutflowForm
from outflows.models import Outflow


class OutflowBalanceSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user-out', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Itau',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )
        self.category = Category.objects.create(user=self.user, name='Mercado')

    def _create_outflow(self, value=Decimal('50.00')):
        return Outflow.objects.create(
            user=self.user,
            title='Compra',
            bank=self.bank,
            category=self.category,
            value=value,
        )

    def test_create_outflow_subtracts_bank_balance(self):
        self._create_outflow(value=Decimal('40.00'))

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('60.00'))

    def test_delete_outflow_restores_bank_balance(self):
        outflow = self._create_outflow(value=Decimal('40.00'))
        outflow.delete()

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))

    def test_edit_outflow_adjusts_bank_balance(self):
        outflow = self._create_outflow(value=Decimal('40.00'))
        outflow.value = Decimal('70.00')
        outflow.save()

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('30.00'))

    def test_validation_uses_calculated_balance_not_stored_field(self):
        Inflow.objects.create(
            user=self.user,
            title='Salario',
            bank=self.bank,
            value=Decimal('30.00'),
        )
        # Simula o campo armazenado dessincronizado (cenario do bug real):
        # saldo calculado = 100 + 30 - 0 = 130, mas balance armazenado = 19.57
        Bank.objects.filter(pk=self.bank.pk).update(balance=Decimal('19.57'))

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.current_balance, Decimal('130.00'))
        self.assertEqual(self.bank.balance, Decimal('19.57'))

        form = OutflowForm(
            data={
                'title': 'Saida valida',
                'bank': self.bank.id,
                'category': self.category.id,
                'value': '50.00',
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_form_rejects_value_above_calculated_balance(self):
        Bank.objects.filter(pk=self.bank.pk).update(balance=Decimal('9999.00'))

        form = OutflowForm(
            data={
                'title': 'Saida acima do saldo',
                'bank': self.bank.id,
                'category': self.category.id,
                'value': '150.00',
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('Saldo insuficiente', form.errors['value'][0])

    def test_pre_save_rejects_outflow_above_available_balance(self):
        outflow = Outflow(
            user=self.user,
            title='Saida acima do saldo',
            bank=self.bank,
            category=self.category,
            value=Decimal('150.00'),
        )

        with self.assertRaises(ValidationError):
            outflow.save()

    def test_pre_save_allows_edit_up_to_available_balance(self):
        outflow = self._create_outflow(value=Decimal('60.00'))
        outflow.value = Decimal('100.00')

        outflow.save()

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('0.00'))

    def test_exact_user_scenario_itaun_bank(self):
        """Reproduz o cenario reportado: saldo de 59.79 aceita saida de 50.00"""
        Inflow.objects.create(
            user=self.user, title='Deposito', bank=self.bank, value=Decimal('36.57'),
        )
        self._create_outflow(value=Decimal('76.78'))
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.current_balance, Decimal('59.79'))
        self.assertEqual(self.bank.balance, Decimal('59.79'))

        Outflow.objects.create(
            user=self.user,
            title='Saida de 50 reais',
            bank=self.bank,
            category=self.category,
            value=Decimal('50.00'),
        )

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('9.79'))
        self.assertEqual(self.bank.current_balance, Decimal('9.79'))
