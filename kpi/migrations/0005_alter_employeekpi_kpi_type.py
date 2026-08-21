import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kpi', '0004_add_bonus_and_salary_advance_kpi'),
    ]

    operations = [
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
                        'kuryer',
                    ],
                },
                on_delete=django.db.models.deletion.PROTECT,
                related_name='employee_kpis',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='employeekpi',
            name='kpi_type',
            field=models.CharField(
                choices=[
                    ('sales_percent', 'Yopilgan buyurtmalar summasidan 5%'),
                    ('experience_percent', 'Bir yildan ortiq staj uchun 5%'),
                    ('salary_percent', 'Oylikdan istalgan foiz'),
                    ('bonus', 'Bonus'),
                    ('salary_advance', 'Oylik hisobidan qarz'),
                    ('instant_reward', 'Mukofot'),
                ],
                max_length=30,
            ),
        ),
    ]
