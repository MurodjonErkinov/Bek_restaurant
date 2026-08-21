from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurant', '0014_alter_order_payment_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name', 'id']},
        ),
        migrations.CreateModel(
            name='PartnerTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('purchase_debt', 'Tovar uchun qarz'), ('payment', 'Hamkorga to‘lov'), ('order_offset', 'Order bilan o‘zaro hisob'), ('adjustment_increase', 'Qarzni oshirish tuzatmasi'), ('adjustment_decrease', 'Qarzni kamaytirish tuzatmasi')], max_length=30)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('description', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_partner_transactions', to=settings.AUTH_USER_MODEL)),
                ('order', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partner_transaction', to='restaurant.order')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='partners.partner')),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]
