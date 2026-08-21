from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0013_simplify_order_status'),
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
                    ('partner_offset', 'Hamkor bilan o‘zaro hisob'),
                ],
                default='cash',
                max_length=20,
            ),
        ),
    ]
