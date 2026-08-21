from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0006_simplify_payment_flow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliveryorder',
            name='courier',
        ),
    ]
