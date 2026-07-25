from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

from restaurant.models import Order, RestaurantTable


class WaiterKPI(models.Model):
    BASE_RATE = Decimal('5.00')
    EXPERIENCE_BONUS_RATE = Decimal('5.00')
    ONE_YEAR = timedelta(days=365)
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='kpi_records',
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'afitsant'},)
    order = models.OneToOneField(Order, related_name='waiter_kpi', on_delete=models.PROTECT)
    table = models.ForeignKey(
        RestaurantTable,
        related_name='kpi_records',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    business_date = models.DateField(db_index=True)
    sales_amount = models.DecimalField(max_digits=12, decimal_places=2)
    base_rate = models.DecimalField(max_digits=5, decimal_places=2, default=BASE_RATE)
    experience_bonus_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


    @classmethod
    def rates_for(cls, waiter, on_date):
        joined_date = timezone.localdate(waiter.date_joined)
        has_experience_bonus = joined_date + cls.ONE_YEAR <= on_date
        bonus_rate = cls.EXPERIENCE_BONUS_RATE if has_experience_bonus else Decimal('0.00')
        return cls.BASE_RATE, bonus_rate, cls.BASE_RATE + bonus_rate

    @classmethod
    def create_for_order(cls, order):
        if order.status != 'closed':
            return None
        if not order.waiter_id or order.waiter.role != 'afitsant':
            raise ValueError('Yopilgan buyurtmaga afitsant biriktirilishi shart.')
        if not order.table_id:
            raise ValueError('Yopilgan buyurtmaga stol biriktirilishi shart.')

        business_datetime = order.closed_at or order.created_at
        business_date = timezone.localdate(business_datetime)
        base_rate, bonus_rate, total_rate = cls.rates_for(order.waiter, business_date)
        commission_amount = (order.total_price * total_rate / Decimal('100')).quantize(Decimal('0.01'))

        kpi, _ = cls.objects.update_or_create(
            order=order,
            defaults={
                'waiter': order.waiter,
                'table': order.table,
                'business_date': business_date,
                'sales_amount': order.total_price,
                'base_rate': base_rate,
                'experience_bonus_rate': bonus_rate,
                'total_rate': total_rate,
                'commission_amount': commission_amount,
            },
        )
        return kpi
