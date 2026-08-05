from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('restaurant', '0007_alter_user_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='salary',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=12,
            ),
        ),
    ]
