from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('kpi', '0001_initial'),
        ('restaurant', '0008_user_salary'),
    ]

    operations = [
        migrations.DeleteModel(
            name='WaiterKPI',
        ),
        migrations.CreateModel(
            name='EmployeeKPI',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'kpi_type',
                    models.CharField(
                        choices=[
                            ('sales_percent', 'Yopilgan buyurtmalar summasidan 5%'),
                            ('experience_percent', 'Bir yildan ortiq staj uchun 5%'),
                            ('salary_percent', 'Oylikdan istalgan foiz'),
                        ],
                        max_length=30,
                    ),
                ),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                (
                    'percentage',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('5.00'),
                        max_digits=5,
                    ),
                ),
                (
                    'base_amount',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.00'),
                        editable=False,
                        max_digits=14,
                    ),
                ),
                (
                    'kpi_amount',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.00'),
                        editable=False,
                        max_digits=14,
                    ),
                ),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='created_employee_kpis',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'employee',
                    models.ForeignKey(
                        limit_choices_to={
                            'role__in': ['admin', 'oshpaz', 'kassir', 'afitsant'],
                        },
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='employee_kpis',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-period_end', '-id'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=(
                            'employee',
                            'kpi_type',
                            'period_start',
                            'period_end',
                        ),
                        name='unique_employee_kpi_period',
                    ),
                ],
            },
        ),
    ]
