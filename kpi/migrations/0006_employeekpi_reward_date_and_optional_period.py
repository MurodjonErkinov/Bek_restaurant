from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kpi', '0005_alter_employeekpi_kpi_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeekpi',
            name='period_start',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employeekpi',
            name='period_end',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeekpi',
            name='reward_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
