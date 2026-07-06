from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Account


@receiver(post_save, sender=User)
def ensure_account_for_user(sender, instance, created, **kwargs):
    if created:
        Account.objects.get_or_create(user=instance, defaults={'name': instance.username})
