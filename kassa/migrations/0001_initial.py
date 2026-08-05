import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('restaurant', '0009_alter_user_role'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CashSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opening_balance', models.DecimalField(decimal_places=2, max_digits=12)),
                ('opened_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('open', 'Ochiq'), ('closed', 'Yopilgan')], default='open', max_length=10)),
                ('closing_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('cashier', models.ForeignKey(limit_choices_to={'role': 'kassir'}, on_delete=django.db.models.deletion.PROTECT, related_name='cash_sessions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CashExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('description', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cash_session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expenses', to='kassa.cashsession')),
            ],
        ),
        migrations.CreateModel(
            name='CashTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('cash_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('credit_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cash_session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='kassa.cashsession')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='cash_transaction', to='restaurant.order')),
            ],
        ),
    ]
