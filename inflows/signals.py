from django.db.models import F
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from banks.models import Bank
from inflows.models import Inflow


@receiver(pre_save, sender=Inflow)
def store_original_inflow_value(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Inflow.objects.get(pk=instance.pk)
            instance._original_value = original.value
        except Inflow.DoesNotExist:
            instance._original_value = instance.value
    else:
        instance._original_value = instance.value


@receiver(post_save, sender=Inflow)
def update_balance_on_inflow(sender, instance, created, **kwargs):
    """Soma o valor do inflow ao balance do banco (criacao) ou ajusta a diferenca (edicao)"""
    if instance.value > 0:
        if created:
            Bank.objects.filter(pk=instance.bank_id).update(balance=F('balance') + instance.value)
        else:
            old_value = getattr(instance, '_original_value', instance.value)
            Bank.objects.filter(pk=instance.bank_id).update(
                balance=F('balance') + instance.value - old_value
            )


@receiver(post_delete, sender=Inflow)
def remove_balance_on_inflow_delete(sender, instance, **kwargs):
    """Subtrai do banco o valor de uma entrada excluida"""
    if instance.value > 0 and instance.bank_id:
        Bank.objects.filter(pk=instance.bank_id).update(balance=F('balance') - instance.value)
