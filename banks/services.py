from django.db import transaction

from banks.models import Bank


def reconcile_bank_balances():
    updated = []
    for bank in Bank.objects.all().order_by('pk'):
        with transaction.atomic():
            locked_bank = Bank.objects.select_for_update().get(pk=bank.pk)
            calculated_balance = locked_bank.current_balance
            if locked_bank.balance != calculated_balance:
                locked_bank.balance = calculated_balance
                locked_bank.save(update_fields=['balance', 'update_at'])
                updated.append({'id': locked_bank.pk, 'balance': str(calculated_balance)})
    return updated
