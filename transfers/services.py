from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from banks.models import Bank

from .models import BankTransfer


def create_bank_transfer(*, user, source_bank, destination_bank, value, title=None):
    """Create one transfer and update both bank balances atomically."""
    source_bank_id = getattr(source_bank, 'pk', source_bank)
    destination_bank_id = getattr(destination_bank, 'pk', destination_bank)

    if source_bank_id == destination_bank_id:
        raise ValidationError('O banco de origem e o banco de destino devem ser diferentes.')

    try:
        value = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError('O valor da transferencia e invalido.')

    if value <= Decimal('0.00'):
        raise ValidationError('O valor da transferencia deve ser maior que zero.')

    with transaction.atomic():
        locked_banks = list(
            Bank.objects.select_for_update()
            .filter(user=user, pk__in=[source_bank_id, destination_bank_id])
            .order_by('pk')
        )
        banks_by_id = {bank.pk: bank for bank in locked_banks}
        source = banks_by_id.get(source_bank_id)
        destination = banks_by_id.get(destination_bank_id)

        if source is None:
            raise ValidationError('O banco de origem nao pertence ao usuario autenticado.')
        if destination is None:
            raise ValidationError('O banco de destino nao pertence ao usuario autenticado.')

        source_balance = source.current_balance
        destination_balance = destination.current_balance
        if value > source_balance:
            raise ValidationError(
                f'Saldo insuficiente! Saldo disponivel: R$ {source_balance}'
            )

        transfer = BankTransfer.objects.create(
            user=user,
            title=title,
            source_bank=source,
            destination_bank=destination,
            value=value,
        )

        # Use the calculated balances so an old stored-balance drift is repaired.
        Bank.objects.filter(pk=source.pk).update(
            balance=source_balance - value,
            update_at=timezone.now(),
        )
        Bank.objects.filter(pk=destination.pk).update(
            balance=destination_balance + value,
            update_at=timezone.now(),
        )

        return transfer
