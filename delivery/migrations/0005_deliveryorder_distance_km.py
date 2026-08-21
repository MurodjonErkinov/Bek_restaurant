from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0004_simplify_delivery_flow'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryorder',
            name='distance_km',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
    ]
