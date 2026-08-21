from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0002_alter_deliveryorder_payment_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliveryorder',
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
