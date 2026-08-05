import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('kpi', '0002_employeekpi_delete_waiterkpi'),
        ('restaurant', '0009_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeekpi',
            name='base_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=14,
            ),
        ),
        migrations.AlterField(
            model_name='employeekpi',
            name='employee',
            field=models.ForeignKey(
                limit_choices_to={
                    'role__in': [
                        'admin',
                        'oshpaz',
                        'kassir',
                        'afitsant',
                        'farrosh',
                        'moykachi',
                    ],
                },
                on_delete=django.db.models.deletion.PROTECT,
                related_name='employee_kpis',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
