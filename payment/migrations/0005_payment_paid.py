from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_payment_parcelas'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='paid',
            field=models.BooleanField(default=False),
        ),
    ]
