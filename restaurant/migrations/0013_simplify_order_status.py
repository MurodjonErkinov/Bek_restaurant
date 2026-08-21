from django.db import migrations, models


def simplify_existing_statuses(apps, schema_editor):
    Order = apps.get_model('restaurant', 'Order')
    Order.objects.filter(status__in=['cooking', 'ready']).update(status='new')


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0012_alter_order_payment_type'),
    ]

    operations = [
        migrations.RunPython(simplify_existing_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[('new', 'Yangi'), ('closed', 'Yopilgan')],
                default='new',
                max_length=20,
            ),
        ),
    ]
