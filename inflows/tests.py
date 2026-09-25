from decimal import Decimal
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from banks.models import Bank
from inflows.models import Inflow
from inflows.services import delete_inflow, register_inflow, update_inflow


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


class InflowServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='inflow-service-user', password='pass123')
        self.other_user = User.objects.create_user(username='inflow-service-other', password='pass123')
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

    def test_register_inflow_updates_balance(self):
        inflow = register_inflow(user=self.user, bank=self.bank, value=Decimal('40.00'), title='Entrada')

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('140.00'))
        self.assertEqual(self.bank.current_balance, Decimal('140.00'))
        self.assertEqual(inflow.value, Decimal('40.00'))

    def test_register_inflow_rejects_foreign_bank(self):
        with self.assertRaises(ValidationError):
            register_inflow(user=self.user, bank=self.foreign_bank, value=Decimal('10.00'))

    def test_update_inflow_moves_balance_to_new_bank(self):
        inflow = register_inflow(user=self.user, bank=self.bank, value=Decimal('40.00'))
        update_inflow(user=self.user, inflow=inflow, value=Decimal('20.00'), title='Entrada nova', bank=self.second_bank)

        self.bank.refresh_from_db()
        self.second_bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))
        self.assertEqual(self.second_bank.balance, Decimal('70.00'))

    def test_delete_inflow_restores_balance(self):
        inflow = register_inflow(user=self.user, bank=self.bank, value=Decimal('30.00'))
        delete_inflow(user=self.user, inflow=inflow)

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('100.00'))
        self.assertEqual(self.bank.current_balance, Decimal('100.00'))


class InflowListFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='inflow-filter-user', password='pass123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco filtro',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )
        self.client.force_login(self.user)

    def _create_inflow(self, title, month, year):
        inflow = Inflow.objects.create(user=self.user, title=title, bank=self.bank, value=Decimal('10.00'))
        Inflow.objects.filter(pk=inflow.pk).update(
            created_at=timezone.make_aware(datetime(year, month, 10, 12, 0)),
        )
        return inflow

    def test_inflow_list_filters_by_month_and_year(self):
        self._create_inflow('Janeiro', 1, 2026)
        self._create_inflow('Fevereiro', 2, 2026)
        self._create_inflow('Janeiro do ano anterior', 1, 2025)

        response = self.client.get(reverse('inflow_list'), {'month': '1', 'year': '2026'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item.title for item in response.context['inflows']], ['Janeiro'])

    def test_inflow_list_filters_by_year_only(self):
        self._create_inflow('Janeiro', 1, 2026)
        self._create_inflow('Fevereiro', 2, 2026)
        self._create_inflow('Janeiro do ano anterior', 1, 2025)

        response = self.client.get(reverse('inflow_list'), {'year': '2026'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(item.title for item in response.context['inflows']),
            {'Janeiro', 'Fevereiro'},
        )
