from django.db import migrations, models
from django.conf import settings
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('kpi', '0003_alter_employeekpi_base_amount_and_employee'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='employeekpi',
            name='unique_employee_kpi_period',
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
                ],
                max_length=30,
            ),
        ),
        migrations.AddConstraint(
            model_name='employeekpi',
            constraint=models.UniqueConstraint(
                condition=Q(kpi_type__in=['sales_percent', 'experience_percent', 'salary_percent']),
                fields=('employee', 'kpi_type', 'period_start', 'period_end'),
                name='unique_regular_employee_kpi_period',
            ),
        ),
    ]
