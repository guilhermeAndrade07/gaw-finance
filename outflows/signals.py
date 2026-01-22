from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from outflows.models import Outflow


@receiver(pre_save, sender=Outflow)
def validate_outflow_balance(sender, instance, **kwargs):
    """Valida se o valor da saída não é maior que o balance do banco"""
    if instance.value > 0:
        bank = instance.bank
        if instance.value > bank.balance:
            raise ValidationError(
                f'Saldo insuficiente! Balance: {bank.balance}, Valor: {instance.value}'
            )


@receiver(post_save, sender=Outflow)
def update_balance_on_outflow(sender, instance, created, **kwargs):
    """Subtrai o valor do outflow do balance do banco"""
    if created:
        if instance.value > 0:
            bank = instance.bank
            bank.balance -= instance.value
            bank.save()
