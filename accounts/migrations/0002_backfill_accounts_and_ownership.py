from django.db import migrations


def backfill_accounts_and_ownership(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Account = apps.get_model('accounts', 'Account')
    Bank = apps.get_model('banks', 'Bank')
    Category = apps.get_model('categories', 'Category')
    Inflow = apps.get_model('inflows', 'Inflow')
    Outflow = apps.get_model('outflows', 'Outflow')
    Payment = apps.get_model('payment', 'Payment')
    Signature = apps.get_model('signatures', 'Signature')

    users = User.objects.order_by('id')
    first_user = users.first()

    for user in users:
        Account.objects.get_or_create(
            user=user,
            defaults={'user_number': user.username},
        )

    if first_user is None:
        return

    Bank.objects.filter(user__isnull=True).update(user=first_user)
    Category.objects.filter(user__isnull=True).update(user=first_user)
    Inflow.objects.filter(user__isnull=True).update(user=first_user)
    Outflow.objects.filter(user__isnull=True).update(user=first_user)
    Payment.objects.filter(user__isnull=True).update(user=first_user)
    Signature.objects.filter(user__isnull=True).update(user=first_user)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('banks', '0003_bank_user'),
        ('categories', '0002_category_user'),
        ('inflows', '0006_inflow_user'),
        ('outflows', '0004_outflow_user'),
        ('payment', '0006_payment_user'),
        ('signatures', '0002_signature_user'),
    ]

    operations = [
        migrations.RunPython(backfill_accounts_and_ownership, migrations.RunPython.noop),
    ]
