from django.db import migrations, models
from django.db.models import Q


def backfill_main_bank(apps, schema_editor):
    Bank = apps.get_model('banks', 'Bank')

    user_ids = Bank.objects.filter(user__isnull=False).values_list('user_id', flat=True).distinct()
    for user_id in user_ids:
        first_bank = Bank.objects.filter(user_id=user_id).order_by('created_at', 'pk').first()
        if first_bank and not first_bank.is_main:
            Bank.objects.filter(pk=first_bank.pk).update(is_main=True)


def reverse_backfill(apps, schema_editor):
    # Reversivel: apenas limpa a flag (sem alterar dados financeiros)
    Bank = apps.get_model('banks', 'Bank')
    Bank.objects.filter(is_main=True).update(is_main=False)


class Migration(migrations.Migration):

    dependencies = [
        ('banks', '0007_resync_balances'),
    ]

    operations = [
        migrations.AddField(
            model_name='bank',
            name='is_main',
            field=models.BooleanField(default=False),
        ),
        # Backfill antes da constraint para garantir um principal por usuario
        migrations.RunPython(backfill_main_bank, reverse_backfill),
        migrations.AddConstraint(
            model_name='bank',
            constraint=models.UniqueConstraint(
                condition=Q(is_main=True),
                fields=['user'],
                name='unique_main_bank_per_user',
            ),
        ),
    ]
