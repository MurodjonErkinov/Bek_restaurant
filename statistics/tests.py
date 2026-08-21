from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from kassa.models import CashExpense, CashSession, CashTransaction
from restaurant.models import (
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
    RestaurantTable,
    User,
)


class StatisticsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            phone='901111111',
            password='password',
            role='admin',
            is_staff=True,
        )
        self.cashier = User.objects.create_user(
            username='cashier',
            phone='902222222',
            password='password',
            role='kassir',
            salary=Decimal('3000000.00'),
        )
        self.waiter = User.objects.create_user(
            username='waiter',
            phone='903333333',
            password='password',
            role='afitsant',
            salary=Decimal('2500000.00'),
        )
        customer_user = User.objects.create_user(
            username='customer',
            phone='904444444',
            password='password',
            role='customer',
        )
        self.customer = Customer.objects.create(
            user=customer_user,
            full_name='Customer',
            phone='904444444',
        )
        category = Category.objects.create(name='Taom')
        self.closed_product = Product.objects.create(
            category=category,
            name='Yopilgan mahsulot',
            price=Decimal('100.00'),
        )
        self.open_product = Product.objects.create(
            category=category,
            name='Ochiq mahsulot',
            price=Decimal('200.00'),
        )
        self.table = RestaurantTable.objects.create(number=1)
        self.client.force_authenticate(self.admin)

    def test_overview_uses_closed_sales_period_expenses_and_real_cash_difference(self):
        closed_order = Order.objects.create(
            customer=self.customer,
            waiter=self.waiter,
            table=self.table,
            status='closed',
            total_price=Decimal('100.00'),
            paid_amount=Decimal('100.00'),
            is_paid=True,
            closed_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=closed_order,
            product=self.closed_product,
            quantity=1,
            price=Decimal('100.00'),
        )
        open_order = Order.objects.create(
            customer=self.customer,
            waiter=self.waiter,
            table=self.table,
            status='new',
            total_price=Decimal('200.00'),
        )
        OrderItem.objects.create(
            order=open_order,
            product=self.open_product,
            quantity=1,
            price=Decimal('200.00'),
        )
        session = CashSession.objects.create(
            cashier=self.cashier,
            opening_balance=Decimal('500.00'),
            status='closed',
            closing_balance=Decimal('600.00'),
            closed_at=timezone.now(),
        )
        CashTransaction.objects.create(
            cash_session=session,
            order=closed_order,
            order_total=Decimal('100.00'),
            cash_amount=Decimal('100.00'),
        )
        current_expense = CashExpense.objects.create(
            cash_session=session,
            amount=Decimal('10.00'),
            description='Bugungi xarajat',
        )
        old_expense = CashExpense.objects.create(
            cash_session=session,
            amount=Decimal('30.00'),
            description='Eski xarajat',
        )
        yesterday = timezone.now() - timedelta(days=1)
        CashExpense.objects.filter(pk=old_expense.pk).update(created_at=yesterday)

        today = timezone.localdate()
        response = self.client.get(
            '/api/statistics/overview/',
            {
                'period_start': today.isoformat(),
                'period_end': today.isoformat(),
                'group_by': 'day',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['sales_total'], Decimal('100.00'))
        self.assertEqual(response.data['summary']['expenses_total'], Decimal('10.00'))
        self.assertEqual(response.data['summary']['kassa_difference'], Decimal('40.00'))
        self.assertEqual(response.data['period_totals'][0]['sales_total'], Decimal('100.00'))
        self.assertEqual(response.data['waiter_stats'][0]['sales_total'], Decimal('100.00'))
        self.assertEqual(response.data['table_stats'][0]['sales_total'], Decimal('100.00'))
        self.assertEqual(len(response.data['top_products']), 1)
        self.assertEqual(
            response.data['top_products'][0]['product__name'],
            self.closed_product.name,
        )
        self.assertEqual(current_expense.amount, Decimal('10.00'))

    def test_kpi_statistics_include_active_employee_without_kpi(self):
        today = timezone.localdate()
        response = self.client.get(
            '/api/statistics/kpi/',
            {
                'period_start': today.replace(day=1).isoformat(),
                'period_end': today.isoformat(),
                'employee': self.waiter.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['employees_count'], 1)
        self.assertEqual(response.data['summary']['kpi_count'], 0)
        employee = response.data['employee_summary'][0]
        self.assertEqual(employee['employee_id'], self.waiter.id)
        self.assertEqual(employee['salary_base'], Decimal('2500000.00'))
        self.assertEqual(employee['total_kpi_amount'], Decimal('0.00'))
        self.assertEqual(employee['total_available_amount'], Decimal('2500000.00'))
