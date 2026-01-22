from django.db.models.signals import post_save
from django.dispatch import receiver
from inflows.models import Inflow


@receiver(post_save, sender=Inflow)
def update_balance_on_inflow(sender, instance, created, **kwargs):
    """Soma o valor do inflow ao balance do banco"""
    if created:
        if instance.value > 0:
            bank = instance.bank
            bank.balance += instance.value
            bank.save()
