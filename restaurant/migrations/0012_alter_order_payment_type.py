from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0011_alter_order_payment_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_type',
            field=models.CharField(
                choices=[
                    ('cash', 'Naqd'),
                    ('card', 'Karta'),
                    ('credit', 'Qarz'),
                    ('mixed', 'Aralash'),
                ],
                default='cash',
                max_length=20,
            ),
        ),
    ]
