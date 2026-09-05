from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from banks.models import Bank
from inflows.models import Inflow
from outflows.models import Outflow

from .models import BankTransfer
from .services import create_bank_transfer


class BankTransferTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='transfer-user', password='pass123')
        self.other_user = User.objects.create_user(username='other-user', password='pass123')
        self.source = Bank.objects.create(
            user=self.user,
            name='Origem',
            account_type='Corrente',
            agency=1,
            account=11,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )
        self.destination = Bank.objects.create(
            user=self.user,
            name='Destino',
            account_type='Poupanca',
            agency=2,
            account=22,
            initial_balance=Decimal('50.00'),
            balance=Decimal('50.00'),
        )

    def test_transfer_is_one_operation_and_updates_both_balances(self):
        transfer = create_bank_transfer(
            user=self.user,
            source_bank=self.source,
            destination_bank=self.destination,
            value=Decimal('40.00'),
            title='Reserva',
        )

        self.assertEqual(BankTransfer.objects.count(), 1)
        self.assertFalse(Inflow.objects.exists())
        self.assertFalse(Outflow.objects.exists())

        self.source.refresh_from_db()
        self.destination.refresh_from_db()
        self.assertEqual(self.source.balance, Decimal('60.00'))
        self.assertEqual(self.destination.balance, Decimal('90.00'))
        self.assertEqual(self.source.current_balance, Decimal('60.00'))
        self.assertEqual(self.destination.current_balance, Decimal('90.00'))
        self.assertEqual(transfer.source_bank_id, self.source.pk)
        self.assertEqual(transfer.destination_bank_id, self.destination.pk)

    def test_transfer_rejects_insufficient_balance(self):
        with self.assertRaises(ValidationError):
            create_bank_transfer(
                user=self.user,
                source_bank=self.source,
                destination_bank=self.destination,
                value=Decimal('100.01'),
            )

        self.assertFalse(BankTransfer.objects.exists())

    def test_transfer_rejects_same_bank(self):
        with self.assertRaises(ValidationError):
            create_bank_transfer(
                user=self.user,
                source_bank=self.source,
                destination_bank=self.source,
                value=Decimal('10.00'),
            )

    def test_transfer_rejects_bank_from_another_user(self):
        foreign_bank = Bank.objects.create(
            user=self.other_user,
            name='Outro',
            account_type='Corrente',
            agency=3,
            account=33,
            initial_balance=Decimal('100.00'),
            balance=Decimal('100.00'),
        )

        with self.assertRaises(ValidationError):
            create_bank_transfer(
                user=self.user,
                source_bank=self.source,
                destination_bank=foreign_bank,
                value=Decimal('10.00'),
            )

        self.assertFalse(BankTransfer.objects.exists())

    def test_create_view_registers_transfer(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('transfer_create'),
            data={
                'title': 'Reserva',
                'source_bank': self.source.pk,
                'destination_bank': self.destination.pk,
                'value': '25.00',
            },
        )

        transfer = BankTransfer.objects.get()
        self.assertRedirects(response, reverse('transfer_detail', kwargs={'pk': transfer.pk}))

    def test_api_creates_and_lists_only_user_transfers(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.post(
            reverse('transfer-create-list-api-view'),
            {
                'title': 'API',
                'source_bank': self.source.pk,
                'destination_bank': self.destination.pk,
                'value': '15.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        listing = client.get(reverse('transfer-create-list-api-view'))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
