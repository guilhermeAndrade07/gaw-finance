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


def user_has_main_bank(user, exclude_pk=None):
    """Retorna True se o usuario ja possui um banco principal."""
    queryset = Bank.objects.filter(user=user, is_main=True)
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    return queryset.exists()


def set_main_bank(user, bank):
    """Define ``bank`` como o banco principal do usuario.

    Demais bancos do usuario perdem a flag principal. Executa dentro de uma
    transacao atomica com lock na linha alvo, evitando condicoes de corrida
    que violariam a constraint ``unique_main_bank_per_user`` (pois removemos a
    flag dos demais antes de promover o alvo).
    """
    with transaction.atomic():
        Bank.objects.filter(user=user, is_main=True).exclude(pk=bank.pk).update(is_main=False)
        locked_bank = Bank.objects.select_for_update().get(pk=bank.pk, user=user)
        if not locked_bank.is_main:
            locked_bank.is_main = True
            locked_bank.save(update_fields=['is_main', 'update_at'])
    return locked_bank


def ensure_main_bank(user, bank):
    """Garante que o usuario possua um banco principal.

    Usado na criacao/edicao de bancos: se o usuario ainda nao tiver nenhum
    banco principal (ex.: primeiro banco cadastrado), promove ``bank``.
    """
    if user is None or user.pk is None:
        return None
    if not user_has_main_bank(user, exclude_pk=bank.pk):
        return set_main_bank(user, bank)
    return None
