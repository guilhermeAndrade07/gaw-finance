from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from banks.models import Bank
from categories.models import Category
from inflows.models import Inflow
from outflows.models import Outflow

from .models import InvestmentAsset, InvestmentMovement


class InvestmentFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='investidor', password='senha-123')
        self.bank = Bank.objects.create(
            user=self.user,
            name='Banco Principal',
            account_type='Corrente',
            agency=1234,
            account=56789,
            initial_balance=Decimal('5000.00'),
            balance=Decimal('5000.00'),
        )

    def test_create_investment_with_initial_apport_generates_outflow_and_movement(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('investment_create'),
            data={
                'name': 'CDB Banco Azul',
                'asset_type': InvestmentAsset.FIXED_INCOME,
                'subtype': 'CDB',
                'institution': 'Banco Azul',
                'bank': self.bank.id,
                'maturity_date': '2027-05-01',
                'expected_rate': '110% do CDI',
                'liquidity_type': InvestmentAsset.AT_MATURITY,
                'current_value': '0',
                'initial_amount': '1000.00',
                'initial_date': '2026-05-08',
                'register_cash_flow': 'on',
                'notes': 'Primeiro aporte',
                'is_active': 'on',
            },
        )

        asset = InvestmentAsset.objects.get(name='CDB Banco Azul')
        self.assertRedirects(response, reverse('investment_detail', kwargs={'pk': asset.pk}))
        self.assertEqual(asset.current_value, Decimal('1000.00'))
        self.assertTrue(InvestmentMovement.objects.filter(asset=asset, operation_type=InvestmentMovement.APPORTION).exists())
        self.assertTrue(Outflow.objects.filter(user=self.user, title__icontains='Aporte em investimento').exists())
        self.assertTrue(Category.objects.filter(user=self.user, name='Investimento').exists())

        self.bank.refresh_from_db()
        self.assertEqual(self.bank.balance, Decimal('4000.00'))

    def test_redemption_generates_inflow_and_updates_asset_value(self):
        asset = InvestmentAsset.objects.create(
            user=self.user,
            bank=self.bank,
            name='Tesouro Selic',
            asset_type=InvestmentAsset.FIXED_INCOME,
            subtype='Tesouro',
            current_value=Decimal('1000.00'),
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('investment_movement_create'),
            data={
                'asset': asset.id,
                'operation_type': InvestmentMovement.REDEMPTION,
                'value': '250.00',
                'movement_date': '2026-05-08',
                'register_cash_flow': 'on',
                'notes': 'Resgate parcial',
            },
        )

        self.assertRedirects(response, reverse('investment_detail', kwargs={'pk': asset.pk}))
        asset.refresh_from_db()
        self.bank.refresh_from_db()

        self.assertEqual(asset.current_value, Decimal('750.00'))
        self.assertTrue(Inflow.objects.filter(user=self.user, title__icontains='Resgate de investimento').exists())
        self.assertEqual(self.bank.balance, Decimal('5250.00'))
