from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Account


@receiver(post_save, sender=User)
def ensure_account_for_user(sender, instance, created, **kwargs):
    defaults = {'name': instance.username}
    account, _ = Account.objects.get_or_create(user=instance, defaults=defaults)

    if created:
        return

    if account.name != instance.username and not Account.objects.filter(name=instance.username).exclude(pk=account.pk).exists():
        account.name = instance.username
        account.save(update_fields=['name', 'updated_at'])
