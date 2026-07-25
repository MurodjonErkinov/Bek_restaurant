from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum
from restaurant.models import Order


class CashSession(models.Model):
    STATUS_CHOICES = [
        ('open', 'Ochiq'),
        ('closed', 'Yopilgan'),
    ]

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='cash_sessions',
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'kassir'},
    )
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    opened_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def report(self):
        transaction_totals = self.transactions.aggregate(
            cash_income=Sum('cash_amount'),
            credit_sales=Sum('credit_amount'),
            sales_total=Sum('order_total'),
        )
        expenses_total = self.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        cash_income = transaction_totals['cash_income'] or Decimal('0.00')
        credit_sales = transaction_totals['credit_sales'] or Decimal('0.00')
        sales_total = transaction_totals['sales_total'] or Decimal('0.00')
        expected_balance = self.opening_balance + cash_income - expenses_total
        difference = None
        if self.closing_balance is not None:
            difference = self.closing_balance - expected_balance

        return {
            'session_id': self.id,
            'cashier_id': self.cashier_id,
            'status': self.status,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at,
            'opening_balance': self.opening_balance,
            'orders_count': self.transactions.count(),
            'sales_total': sales_total,
            'cash_income': cash_income,
            'credit_sales': credit_sales,
            'expenses_total': expenses_total,
            'expected_balance': expected_balance,
            'closing_balance': self.closing_balance,
            'difference': difference,
        }


class CashTransaction(models.Model):
    cash_session = models.ForeignKey(CashSession, related_name='transactions', on_delete=models.PROTECT)
    order = models.OneToOneField(Order, related_name='cash_transaction', on_delete=models.PROTECT)
    order_total = models.DecimalField(max_digits=12, decimal_places=2)
    cash_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)


class CashExpense(models.Model):
    cash_session = models.ForeignKey(CashSession, related_name='expenses', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
