from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from auditing import actions
from auditing.services import record_audit_event
from banks.models import Bank
from inflows.models import Inflow


def _normalize_value(value):
    try:
        normalized = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError('O valor da entrada e invalido.')
    if normalized <= Decimal('0.00'):
        raise ValidationError('O valor da entrada deve ser maior que zero.')
    return normalized


def _lock_banks(user, bank_ids):
    banks = Bank.objects.select_for_update().filter(
        user=user, pk__in=bank_ids,
    ).order_by('pk')
    locked_banks = list(banks)
    banks_by_id = {bank.pk: bank for bank in locked_banks}
    for bank_id in bank_ids:
        if banks_by_id.get(bank_id) is None:
            raise ValidationError('O banco informado nao pertence ao usuario autenticado.')
    return banks_by_id


def _sync_bank(bank):
    bank.refresh_from_db()
    bank.balance = bank.current_balance
    bank.save(update_fields=['balance', 'update_at'])


def register_inflow(*, user, bank, value, title=None):
    try:
        value = _normalize_value(value)
    except ValidationError:
        raise
    bank_id = bank.pk

    with transaction.atomic():
        banks = _lock_banks(user, [bank_id])
        locked_bank = banks[bank_id]
        _sync_bank(locked_bank)

        instance = Inflow(user=user, title=title, bank=locked_bank, value=value)
        instance._balance_service_managed = True
        instance.full_clean()
        instance.save()
        _sync_bank(locked_bank)
        record_audit_event(
            action=actions.INFLOW_CREATE,
            user=user,
            resource_type='Inflow',
            resource_id=instance.pk,
            description='Entrada registrada.',
            metadata={'value': str(value), 'bank_id': locked_bank.pk},
        )
        return instance


def update_inflow(*, user, inflow, value, title=None, bank=None):
    if not inflow.pk:
        raise ValidationError('A entrada informada nao existe.')
    original = Inflow.objects.get(pk=inflow.pk)
    if original.user_id != user.id:
        raise ValidationError('A entrada nao pertence ao usuario autenticado.')

    target_bank = bank or original.bank
    bank_id = target_bank.pk
    value = _normalize_value(value)
    title = title if title is not None else original.title

    with transaction.atomic():
        banks = _lock_banks(user, [original.bank_id, bank_id])
        locked_new_bank = banks[bank_id]

        original.bank = locked_new_bank
        original.title = title
        original.value = value
        original._balance_service_managed = True
        original.full_clean()
        original.save()

        for locked_bank in banks.values():
            _sync_bank(locked_bank)
        record_audit_event(
            action=actions.INFLOW_UPDATE,
            user=user,
            resource_type='Inflow',
            resource_id=original.pk,
            description='Entrada atualizada.',
            metadata={'value': str(value), 'bank_id': bank_id},
        )
        return original


def delete_inflow(*, user, inflow):
    if inflow.user_id != user.id:
        raise ValidationError('A entrada nao pertence ao usuario autenticado.')
    bank_id = inflow.bank_id

    with transaction.atomic():
        banks = _lock_banks(user, [bank_id])
        inflow._balance_service_managed = True
        inflow.delete()
        _sync_bank(banks[bank_id])
        record_audit_event(
            action=actions.INFLOW_DELETE,
            user=user,
            resource_type='Inflow',
            resource_id=inflow.pk,
            description='Entrada excluida.',
            metadata={'bank_id': bank_id},
        )
        return True
