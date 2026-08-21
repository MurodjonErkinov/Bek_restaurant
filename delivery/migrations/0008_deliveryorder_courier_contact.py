from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0007_remove_deliveryorder_courier'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryorder',
            name='courier_name',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='deliveryorder',
            name='courier_phone',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
    ]
