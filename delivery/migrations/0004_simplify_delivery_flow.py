from django.db import migrations, models


def simplify_existing_statuses(apps, schema_editor):
    DeliveryOrder = apps.get_model('delivery', 'DeliveryOrder')
    DeliveryOrder.objects.filter(status__in=['confirmed', 'cooking', 'ready']).update(status='new')


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0003_alter_deliveryorder_payment_type'),
    ]

    operations = [
        migrations.RunPython(simplify_existing_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='deliveryorder',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Yangi'),
                    ('on_the_way', 'Yo‘lda'),
                    ('delivered', 'Yetkazildi'),
                    ('cancelled', 'Bekor qilingan'),
                ],
                default='new',
                max_length=20,
            ),
        ),
        migrations.RemoveField(model_name='deliveryorder', name='estimated_delivery_time'),
        migrations.RemoveField(model_name='deliveryorder', name='confirmed_at'),
        migrations.RemoveField(model_name='deliveryorder', name='cooking_started_at'),
        migrations.RemoveField(model_name='deliveryorder', name='ready_at'),
    ]
