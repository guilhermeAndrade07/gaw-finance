from decimal import Decimal
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from banks.models import Bank
from categories.models import Category
from inflows.models import Inflow
from outflows.forms import OutflowForm
from outflows.models import Outflow
from outflows.services import delete_outflow, register_outflow, update_outflow


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


class OutflowServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='outflow-service-user', password='pass123')
        self.other_user = User.objects.create_user(username='outflow-service-other', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco service',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )
        self.second_bank = Bank.objects.create(
            user=self.user,
            name='Banco secundario service',
            account_type='Corrente',
            agency=2,
            account=22,
            initial_balance=Decimal('50.00'),
            balance=Decimal('50.00'),
        )
        self.foreign_bank = Bank.objects.create(
            user=self.other_user,
            name='Banco estrangeiro service',
            account_type='Corrente',
            agency=3,
            account=33,
            initial_balance=Decimal('75.00'),
            balance=Decimal('75.00'),
        )
        self.category = Category.objects.create(user=self.user, name='Categoria service')

    def test_register_outflow_updates_balance(self):
        outflow = register_outflow(
            user=self.user,
            bank=self.bank,
            value=Decimal('40.00'),
            title='Saida service',
            category=self.category,
        )

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('60.00'))
        self.assertEqual(self.bank.current_balance, Decimal('60.00'))
        self.assertEqual(outflow.value, Decimal('40.00'))

    def test_register_outflow_rejects_insufficient_balance(self):
        with self.assertRaises(ValidationError):
            register_outflow(user=self.user, bank=self.bank, value=Decimal('150.00'))

    def test_register_outflow_rejects_foreign_bank(self):
        with self.assertRaises(ValidationError):
            register_outflow(user=self.user, bank=self.foreign_bank, value=Decimal('10.00'))

    def test_update_outflow_moves_balance_to_new_bank(self):
        outflow = register_outflow(user=self.user, bank=self.bank, value=Decimal('40.00'))
        update_outflow(
            user=self.user,
            outflow=outflow,
            value=Decimal('20.00'),
            title='Saida service nova',
            bank=self.second_bank,
            category=self.category,
        )

        self.bank.refresh_from_db()
        self.second_bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))
        self.assertEqual(self.second_bank.balance, Decimal('30.00'))

    def test_delete_outflow_restores_balance(self):
        outflow = register_outflow(user=self.user, bank=self.bank, value=Decimal('30.00'))
        delete_outflow(user=self.user, outflow=outflow)

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))
        self.assertEqual(self.bank.current_balance, Decimal('100.00'))


class OutflowListFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='outflow-filter-user', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco filtro',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )
        self.category = Category.objects.create(user=self.user, name='Categoria filtro')
        self.client.force_login(self.user)

    def _create_outflow(self, title, month, year):
        outflow = Outflow.objects.create(
            user=self.user,
            title=title,
            bank=self.bank,
            category=self.category,
            value=Decimal('10.00'),
        )
        Outflow.objects.filter(pk=outflow.pk).update(
            created_at=timezone.make_aware(datetime(year, month, 10, 12, 0)),
        )
        return outflow

    def test_outflow_list_filters_by_month_and_year(self):
        self._create_outflow('Janeiro', 1, 2026)
        self._create_outflow('Fevereiro', 2, 2026)
        self._create_outflow('Janeiro do ano anterior', 1, 2025)

        response = self.client.get(reverse('outflow_list'), {'month': '1', 'year': '2026'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item.title for item in response.context['outflows']], ['Janeiro'])

    def test_outflow_list_filters_by_year_only(self):
        self._create_outflow('Janeiro', 1, 2026)
        self._create_outflow('Fevereiro', 2, 2026)
        self._create_outflow('Janeiro do ano anterior', 1, 2025)

        response = self.client.get(reverse('outflow_list'), {'year': '2026'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(item.title for item in response.context['outflows']),
            {'Janeiro', 'Fevereiro'},
        )
