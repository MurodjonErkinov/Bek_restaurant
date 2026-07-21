from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from restaurant.models import Customer, Order, RestaurantTable, User

from .models import WaiterKPI


class WaiterKPITests(TestCase):
    def setUp(self):
        customer_user = User.objects.create_user(
            username='kpi-customer',
            role='customer',
        )
        self.customer = Customer.objects.create(
            user=customer_user,
            full_name='KPI mijoz',
        )
        self.waiter = User.objects.create_user(
            username='experienced-waiter',
            role='afitsant',
        )
        self.waiter.date_joined = timezone.now() - timedelta(days=366)
        self.waiter.save(update_fields=['date_joined'])
        self.table = RestaurantTable.objects.create(number=10)

    def test_experienced_waiter_gets_ten_percent(self):
        order = Order.objects.create(
            customer=self.customer,
            waiter=self.waiter,
            table=self.table,
            status='closed',
            total_price=Decimal('100000.00'),
            closed_at=timezone.now(),
        )

        kpi = WaiterKPI.create_for_order(order)

        self.assertEqual(kpi.base_rate, Decimal('5.00'))
        self.assertEqual(kpi.experience_bonus_rate, Decimal('5.00'))
        self.assertEqual(kpi.total_rate, Decimal('10.00'))
        self.assertEqual(kpi.commission_amount, Decimal('10000.00'))
        self.assertEqual(kpi.business_date, timezone.localdate(order.closed_at))

    def test_kpi_endpoint_can_filter_by_waiter_and_date(self):
        order = Order.objects.create(
            customer=self.customer,
            waiter=self.waiter,
            table=self.table,
            status='closed',
            total_price=Decimal('50000.00'),
            closed_at=timezone.now(),
        )
        kpi = WaiterKPI.create_for_order(order)

        response = APIClient().get(
            reverse('waiter-kpi-list'),
            {
                'waiter': self.waiter.id,
                'business_date': kpi.business_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], kpi.id)
