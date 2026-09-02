from decimal import Decimal

from django.db.models import F
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from banks.models import Bank
from outflows.models import Outflow


@receiver(pre_save, sender=Outflow)
def validate_outflow_balance(sender, instance, **kwargs):
    """Valida o valor da saida contra o saldo calculado do banco e guarda valor original"""
    if instance.pk and Outflow.objects.filter(pk=instance.pk).exists():
        instance._original_value = Outflow.objects.get(pk=instance.pk).value
    else:
        instance._original_value = Decimal('0')

    if instance.value > 0:
        available = instance.bank.current_balance + instance._original_value
        if instance.value > available:
            raise ValidationError(
                f'Saldo insuficiente! Saldo disponível: R$ {available}, Valor: {instance.value}'
            )


@receiver(post_save, sender=Outflow)
def update_balance_on_outflow(sender, instance, created, **kwargs):
    """Subtrai o valor do outflow do balance do banco (criacao) ou ajusta a diferenca (edicao)"""
    if instance.value > 0:
        if created:
            Bank.objects.filter(pk=instance.bank_id).update(balance=F('balance') - instance.value)
        else:
            old_value = getattr(instance, '_original_value', instance.value)
            Bank.objects.filter(pk=instance.bank_id).update(
                balance=F('balance') + old_value - instance.value
            )


@receiver(post_delete, sender=Outflow)
def restore_balance_on_outflow_delete(sender, instance, **kwargs):
    """Devolve ao banco o valor de uma saida excluida"""
    if instance.value > 0 and instance.bank_id:
        Bank.objects.filter(pk=instance.bank_id).update(balance=F('balance') + instance.value)
