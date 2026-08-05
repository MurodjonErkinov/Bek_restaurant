import re
from collections import Counter

from django.db import migrations, models


def normalize_phones(apps, schema_editor):
    user = apps.get_model('restaurant', 'User')
    normalized = {}
    for account in user.objects.all().only('id', 'phone'):
        digits = re.sub(r'\D', '', account.phone or '')
        if len(digits) == 12 and digits.startswith('998'):
            digits = digits[3:]
        normalized[account.id] = digits if len(digits) == 9 else None
    counts = Counter(phone for phone in normalized.values() if phone)
    for account_id, phone in normalized.items():
        user.objects.filter(id=account_id).update(
            phone=phone if phone and counts[phone] == 1 else None,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('restaurant', '0006_alter_restauranttable_options_alter_product_category'),
    ]

    operations = [
        migrations.RunPython(normalize_phones, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
