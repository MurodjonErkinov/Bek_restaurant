from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0010_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_type',
            field=models.CharField(
                choices=[('cash', 'Naqd'), ('card', 'Karta'), ('credit', 'Qarz')],
                default='cash',
                max_length=20,
            ),
        ),
    ]
