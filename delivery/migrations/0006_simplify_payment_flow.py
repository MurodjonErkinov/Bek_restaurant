from django.db import migrations, models
from django.db.models import F


def simplify_statuses(apps, schema_editor):
    DeliveryOrder = apps.get_model('delivery', 'DeliveryOrder')
    DeliveryOrder.objects.filter(status='delivered').update(status='closed', closed_at=F('delivered_at'))
    DeliveryOrder.objects.filter(status='on_the_way').update(status='new')


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0005_deliveryorder_distance_km'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryorder',
            name='closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(simplify_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='deliveryorder',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Yangi'),
                    ('closed', 'Yopilgan'),
                    ('cancelled', 'Bekor qilingan'),
                ],
                default='new',
                max_length=20,
            ),
        ),
        migrations.RemoveField(
            model_name='deliveryorder',
            name='picked_up_at',
        ),
        migrations.RemoveField(
            model_name='deliveryorder',
            name='delivered_at',
        ),
    ]
