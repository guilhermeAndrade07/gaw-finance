from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from outflows.models import Outflow


@receiver(pre_save, sender=Outflow)
def validate_outflow_balance(sender, instance, **kwargs):
    """Valida se o valor da saida nao e maior que o balance do banco e guarda valor original"""
    if instance.pk:
        try:
            original = Outflow.objects.get(pk=instance.pk)
            instance._original_value = original.value
        except Outflow.DoesNotExist:
            instance._original_value = instance.value
    else:
        instance._original_value = instance.value

    if instance.value > 0:
        bank = instance.bank
        if instance.value > bank.balance:
            raise ValidationError(
                f'Saldo insuficiente! Balance: {bank.balance}, Valor: {instance.value}'
            )


@receiver(post_save, sender=Outflow)
def update_balance_on_outflow(sender, instance, created, **kwargs):
    """Subtrai o valor do outflow do balance do banco (criacao) ou ajusta a diferenca (edicao)"""
    if instance.value > 0:
        bank = instance.bank
        if created:
            bank.balance -= instance.value
        else:
            old_value = getattr(instance, '_original_value', instance.value)
            bank.balance += old_value - instance.value
        bank.save()
