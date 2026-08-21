from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kassa', '0003_cashtransaction_delivery_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashtransaction',
            name='card_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
    ]
