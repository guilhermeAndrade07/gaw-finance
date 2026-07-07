from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment
from .services import assign_invoice_to_payment


@receiver(post_save, sender=Payment)
def assign_invoice_on_create(sender, instance, created, **kwargs):
    """
    Atribui automaticamente a fatura ao payment quando ele e criado via save()
    (nao se aplica a bulk_create, que nao dispara signals).
    """
    if created and instance.card_id and instance.date_payment and not instance.invoice_id:
        assign_invoice_to_payment(instance)
