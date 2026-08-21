from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliveryorder',
            name='payment_type',
            field=models.CharField(
                choices=[('cash', 'Naqd'), ('card', 'Karta'), ('credit', 'Qarz')],
                default='cash',
                max_length=20,
            ),
        ),
    ]
