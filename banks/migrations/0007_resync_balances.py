from django.db import migrations
from django.db.models import Sum


def resync_balances(apps, schema_editor):
    """Recalcula o balance armazenado a partir do historico de transacoes.

    Corrige desvios acumulados por exclusoes de lancamentos realizadas
    antes da criacao dos sinais post_delete.
    """
    Bank = apps.get_model('banks', 'Bank')

    for bank in Bank.objects.all():
        inflows = bank.inflows.aggregate(total=Sum('value'))['total'] or 0
        outflows = bank.outflows.aggregate(total=Sum('value'))['total'] or 0
        expected = bank.initial_balance + inflows - outflows

        if bank.balance != expected:
            bank.balance = expected
            bank.save(update_fields=['balance'])


class Migration(migrations.Migration):

    dependencies = [
        ('banks', '0006_recalculate_stale_balances'),
    ]

    operations = [
        migrations.RunPython(resync_balances, migrations.RunPython.noop),
    ]
