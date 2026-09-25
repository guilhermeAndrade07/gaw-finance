from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from auditing import actions
from auditing.services import record_audit_event
from banks.models import Bank
from outflows.models import Outflow


def _normalize_value(value):
    try:
        normalized = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError('O valor da saida e invalido.')
    if normalized <= Decimal('0.00'):
        raise ValidationError('O valor da saida deve ser maior que zero.')
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


def _validate_category(user, category):
    if category is None:
        return None
    if category.user_id != user.id:
        raise ValidationError('A categoria informada nao pertence ao usuario autenticado.')
    return category


def _sync_bank(bank):
    bank.refresh_from_db()
    bank.balance = bank.current_balance
    bank.save(update_fields=['balance', 'update_at'])


def register_outflow(*, user, bank, value, title=None, category=None):
    try:
        value = _normalize_value(value)
    except ValidationError:
        raise
    category = _validate_category(user, category)
    bank_id = bank.pk

    with transaction.atomic():
        banks = _lock_banks(user, [bank_id])
        locked_bank = banks[bank_id]
        _sync_bank(locked_bank)
        available_balance = locked_bank.current_balance
        if value > available_balance:
            raise ValidationError(
                f'Saldo insuficiente! Saldo disponivel: R$ {available_balance}'
            )

        instance = Outflow(
            user=user,
            title=title,
            bank=locked_bank,
            category=category,
            value=value,
        )
        instance._balance_service_managed = True
        instance.full_clean()
        instance.save()
        _sync_bank(locked_bank)
        record_audit_event(
            action=actions.OUTFLOW_CREATE,
            user=user,
            resource_type='Outflow',
            resource_id=instance.pk,
            description='Saida registrada.',
            metadata={'value': str(value), 'bank_id': locked_bank.pk, 'category_id': category.pk if category else None},
        )
        return instance


def update_outflow(*, user, outflow, value, title=None, bank=None, category=None):
    if not outflow.pk:
        raise ValidationError('A saida informada nao existe.')
    original = Outflow.objects.get(pk=outflow.pk)
    if original.user_id != user.id:
        raise ValidationError('A saida nao pertence ao usuario autenticado.')

    target_bank = bank or original.bank
    bank_id = target_bank.pk
    value = _normalize_value(value)
    category = _validate_category(user, category or original.category)
    title = title if title is not None else original.title

    with transaction.atomic():
        banks = _lock_banks(user, [original.bank_id, bank_id])
        locked_new_bank = banks[bank_id]

        original.bank = locked_new_bank
        original.category = category
        original.title = title
        original.value = value
        original._balance_service_managed = True
        original.full_clean()
        original.save()

        for locked_bank in banks.values():
            _sync_bank(locked_bank)
        record_audit_event(
            action=actions.OUTFLOW_UPDATE,
            user=user,
            resource_type='Outflow',
            resource_id=original.pk,
            description='Saida atualizada.',
            metadata={'value': str(value), 'bank_id': bank_id},
        )
        return original


def delete_outflow(*, user, outflow):
    if outflow.user_id != user.id:
        raise ValidationError('A saida nao pertence ao usuario autenticado.')
    bank_id = outflow.bank_id

    with transaction.atomic():
        banks = _lock_banks(user, [bank_id])
        outflow._balance_service_managed = True
        outflow.delete()
        _sync_bank(banks[bank_id])
        record_audit_event(
            action=actions.OUTFLOW_DELETE,
            user=user,
            resource_type='Outflow',
            resource_id=outflow.pk,
            description='Saida excluida.',
            metadata={'bank_id': bank_id},
        )
        return True
