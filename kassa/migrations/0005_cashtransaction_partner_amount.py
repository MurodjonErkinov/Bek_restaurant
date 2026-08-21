from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kassa', '0004_cashtransaction_card_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashtransaction',
            name='partner_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
    ]
