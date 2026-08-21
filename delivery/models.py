from decimal import Decimal, ROUND_CEILING

from django.conf import settings
from django.db import models

from restaurant.models import Customer, Product


class DeliveryOrder(models.Model):
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('closed', 'Yopilgan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    PAYMENT_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('credit', 'Qarz'),
        ('mixed', 'Aralash'),
    ]

    customer = models.ForeignKey(Customer, related_name='delivery_orders', on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_delivery_orders',
        on_delete=models.PROTECT,
    )
    courier_name = models.CharField(max_length=150)
    courier_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    debt_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_delivery_fee(self):
        if self.distance_km is None:
            return self.delivery_fee
        extra_distance = max(self.distance_km - Decimal('1.00'), Decimal('0.00'))
        charged_km = extra_distance.to_integral_value(rounding=ROUND_CEILING)
        return charged_km * Decimal('5000.00')

    def save(self, *args, **kwargs):
        self.delivery_fee = self.calculate_delivery_fee()
        self.total_price = max(
            self.subtotal + self.delivery_fee - self.discount,
            Decimal('0.00'),
        )
        update_fields = kwargs.get('update_fields')
        if update_fields and {'distance_km', 'subtotal', 'discount'}.intersection(update_fields):
            kwargs['update_fields'] = set(update_fields) | {'delivery_fee', 'total_price'}
        super().save(*args, **kwargs)


class DeliveryOrderItem(models.Model):
    delivery_order = models.ForeignKey(DeliveryOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='delivery_order_items', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
