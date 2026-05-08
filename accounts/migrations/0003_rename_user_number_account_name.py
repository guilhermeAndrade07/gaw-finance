from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_backfill_accounts_and_ownership'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='user_number',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='account',
            name='name',
            field=models.CharField(max_length=150, unique=True),
        ),
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': ['name']},
        ),
    ]
