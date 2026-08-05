from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kassa', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='cashsession',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'open')), fields=('cashier',), name='unique_open_cash_session_per_cashier'),
        ),
    ]
