from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class Partner(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self):
        return self.name

    @property
    def balance(self):
        totals = self.transactions.aggregate(
            increases=Sum(
                'amount',
                filter=models.Q(transaction_type__in=['purchase_debt', 'adjustment_increase']),
            ),
            decreases=Sum(
                'amount',
                filter=models.Q(transaction_type__in=['payment', 'order_offset', 'adjustment_decrease']),
            ),
        )
        return (totals['increases'] or Decimal('0.00')) - (
            totals['decreases'] or Decimal('0.00')
        )


class PartnerTransaction(models.Model):
    PURCHASE_DEBT = 'purchase_debt'
    PAYMENT = 'payment'
    ORDER_OFFSET = 'order_offset'
    ADJUSTMENT_INCREASE = 'adjustment_increase'
    ADJUSTMENT_DECREASE = 'adjustment_decrease'
    TRANSACTION_TYPE_CHOICES = [
        (PURCHASE_DEBT, 'Tovar uchun qarz'),
        (PAYMENT, 'Hamkorga to‘lov'),
        (ORDER_OFFSET, 'Order bilan o‘zaro hisob'),
        (ADJUSTMENT_INCREASE, 'Qarzni oshirish tuzatmasi'),
        (ADJUSTMENT_DECREASE, 'Qarzni kamaytirish tuzatmasi'),
    ]

    partner = models.ForeignKey(Partner, related_name='transactions', on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    order = models.OneToOneField(
        'restaurant.Order',
        related_name='partner_transaction',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_partner_transactions',
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
